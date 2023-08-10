from copy import copy
import cv2
import pandas as pd
import numpy as np
from scipy import stats
import keras_ocr
from sklearn.cluster import DBSCAN
from configs import *


class TextSearcher:
    def __init__(self):
        self.mask = None
        self.write_log = False
        self.text_box_reduction_coefficient_x = 0
        self.text_box_reduction_coefficient_y = 0
        self.width = 0
        self.height = 0
        self.prediction_results = None
        self.text = []
        self.line_thickness = self.line_thickness = CONFIGS['TextReader']['LineThickness']
        self.pipeline = keras_ocr.pipeline.Pipeline(scale=CONFIGS['TextReader']['ImageScale'])

    def empty_prediction_results(self):
        self.mask = None
        self.prediction_results = None
        self.text = []

    def read_image(self, image: np.array):
        self.height = image.shape[0]
        self.width = image.shape[1]
        self.text_box_reduction_coefficient_x = self.width * 0.04
        self.text_box_reduction_coefficient_y = self.height * 0.05
        self.prediction_results = self.pipeline.recognize([image])

    def draw_boxes(self, image: np.array):
        for details in self.text:
            x1, y1, x2, y2 = details['x1'], details['y1'], details['x2'], details['y2']
            cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), self.line_thickness)

    def erase_text(self, image):
        for details in self.text:
            x1, y1, x2, y2 = details['x1'], details['y1'], details['x2'], details['y2']
            for step in range(5):
                if y1 - 1 > 0:
                    y1 -= 1
                if x1 - 1 > 0:
                    x1 -= 1
            color_to_paint = stats.mode(image[y1:y2+5, x1:x2+5], keepdims=True).mode[0][0]
            image[y1:y2, x1:x2] = color_to_paint

    def write_prediction_details(self, details='', page=0):
        for text, box in self.prediction_results[0]:
            x1, y1, x2, y2 = int(box[0][0]), int(box[0][1]), int(box[1][0]), int(box[2][1])
            self.text.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'text': text})

    def clean_big_text_boxes(self):
        text = pd.DataFrame(self.text)
        index_to_delete = []
        for index in text.index:
            x1, x2, y1, y2, txt = text['x1'][index], text['x2'][index], text['y1'][index], text['y2'][index], \
                text['text'][index]

            if x2-x1 > len(txt) * self.text_box_reduction_coefficient_x:
                index_to_delete.append(index)

        text.drop(index_to_delete, inplace=True)
        self.text = [{'x1': row[0], 'y1': row[1], 'x2': row[2], 'y2': row[3], 'text': row[4]} for row in text.values]

    def clean_text_boxes(self, text_results=None):
        if text_results is None:
            text = pd.DataFrame(self.text)
        else:
            text = pd.DataFrame(text_results)
        index_to_delete = []

        text['S'] = (text['x2'] - text['x1']) * (text['y2'] - text['y1'])
        text.sort_values('S', ascending=False, inplace=True)
        for index in text.sort_values('S').index:
            x1, x2, y1, y2, s = text['x1'][index], text['x2'][index], text['y1'][index], text['y2'][index], text['S'][index]
            x1 = x1 - (self.text_box_reduction_coefficient_x / 2)
            x2 = x2 + (self.text_box_reduction_coefficient_x / 2)
            y1 = y1 - (self.text_box_reduction_coefficient_y / 3)
            y2 = y2 + (self.text_box_reduction_coefficient_y / 3)
            indexes = text.index.where((text['x1'] >= x1) & (text['x2'] <= x2)
                                       &
                                       (text['y1'] >= y1) & (text['y2'] <= y2)
                                       &
                                       (text['S'] <= s)).dropna()
            for ind in indexes:
                if ind != index:
                    index_to_delete.append(ind)

        text.sort_index(inplace=True)
        text.drop(index_to_delete, inplace=True)
        if text_results is None:
            self.text = []
            for row in text.values:
                unique_text = []
                for text_values in row[4].split():
                    if text_values not in unique_text:
                        unique_text.append(text_values)
                self.text.append({'x1': row[0], 'y1': row[1], 'x2': row[2], 'y2': row[3],
                                  'text': ' '.join(unique_text)})
        else:
            text_results = []
            for row in text.values:
                unique_text = []
                for text_values in row[4].split():
                    if text_values not in unique_text:
                        unique_text.append(text_values)
                text_results.append({'x1': row[0], 'y1': row[1], 'x2': row[2], 'y2': row[3],
                                     'text': ' '.join(unique_text)})
            return text_results

    def refine_text(self):
        text = pd.DataFrame(self.text)
        data = pd.DataFrame(columns=['x1', 'y1', 'x2', 'y2', 'text'])
        current_index = 0
        for word in text.values:
            x1, y1, x2, y2 = word[:4]
            letters_amount = len(word[4])
            letter_size = (x2 - x1) / letters_amount if letters_amount > 1 else x2 - x1
            new_x1 = x1 + letter_size
            data.loc[current_index] = [x1, y1, new_x1, y2, word[4]]
            current_index += 1
            for letter in range(letters_amount - 1):
                data.loc[current_index] = [new_x1, y1, new_x1 + letter_size, y2, word[4]]
                new_x1 += letter_size
                current_index += 1
        eps = 50
        clusters = DBSCAN(eps=eps, min_samples=1).fit(data.values[:, :4])
        labels = clusters.labels_
        data['labels'] = labels
        text_result = []
        # print(data)
        for label in data['labels'].unique():
            text_group = data.where(data['labels'] == label).dropna().sort_values(by=['y1', 'x1']).drop('labels',
                                                                                                        axis='columns')
            sentence = [text_group.values[0]]
            for word in text_group.values:
                if word[4] != sentence[-1][4]:
                    sentence.append(word)
                else:
                    if sentence[-1][1] < word[1]:
                        sentence[-1][1] = word[1]
                    sentence[-1][2] = word[2]
                    sentence[-1][3] = word[3]
            sorted_text = []
            sentence = pd.DataFrame(sentence, columns=['x1', 'y1', 'x2', 'y2', 'text'])
            index = sentence.index[0]
            analyzed_index = []
            while True:
                current_word = sentence.iloc[sentence.index[index]]
                new_index = sentence.where(sentence['y1'] - current_word['y2'] < 1).dropna().index
                index = []
                for ind in new_index:
                    if ind not in analyzed_index:
                        index.append(ind)
                if index:
                    buffer = sentence.take(index).sort_values('x1')
                    for values in buffer.values:
                        sorted_text.append(values[4])
                    for ind in index:
                        analyzed_index.append(ind)
                for ind in sentence.index:
                    if ind not in analyzed_index:
                        analyzed_index.append(ind)
                        index = ind
                        break
                else:
                    break
            text_result.append(
                {
                    'x1': int(text_group['x1'].min()),
                    'y1': int(text_group['y1'].min()),
                    'x2': int(text_group['x2'].max()),
                    'y2': int(text_group['y2'].max()),
                    'text': ' '.join(sorted_text)
                }
            )
        self.text = text_result
