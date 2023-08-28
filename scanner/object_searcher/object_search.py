import cv2
import pandas as pd
from difflib import SequenceMatcher
from image_loader.image_loader import ScreenshotMaker
from configs import *
from .create_mask import create_mask
from .create_mask import redraw_mask


screenshotMaker = ScreenshotMaker()


class ObjectSearcher:
    def __init__(self):
        self.image = None
        self.mask = None
        self.height = None
        self.width = None
        self.lines = []
        self.lines_dict = {}
        self.objects = []
        self.circles = []
        self.min_height = screenshotMaker.region[3] * CONFIGS['ObjectReader']['ObjectMinHeightCoefficient']
        self.min_width = screenshotMaker.region[2] * CONFIGS['ObjectReader']['ObjectMinWidthCoefficient']
        self.line_thickness = CONFIGS['ObjectReader']['LineThickness']
        self.write_log = False

    def empty_objects_data(self):
        self.image = None
        self.mask = None
        self.height = None
        self.width = None
        self.lines = []
        self.lines_dict = {}
        self.objects = []
        self.circles = []

    def find_large_objects(self, mask, start_x=0, start_y=0):
        self.find_horizontal_lines(mask)
        self.find_vertical_lines(mask)
        for key in self.lines_dict.keys():
            y1, y2 = [int(y) for y in key.split('-')]
            for x1, x2 in zip(self.lines_dict[key][::2], self.lines_dict[key][1::2]):
                self.objects.append({'x1': x1+start_x, 'y1': y1+start_y, 'x2': x2+start_x, 'y2': y2+start_y,
                                     'height': y2-y1, 'width': x2-x1})

    def find_small_objects(self):
        old_objects = [obj for obj in self.objects if obj['height'] > self.height * 0.12 and
                       obj['width'] > self.width * 0.7]
        for box in old_objects:
            image_slice = self.image[box['y1']+10:box['y2']-10, box['x1']+10:box['x2']-10]
            mask_slice = redraw_mask(image_slice, create_mask(image_slice, reduce_quality=False))
            self.ungroup_buttons(mask_slice, start_x=box['x1']+10, start_y=box['y1']+10, box=box)
            self.find_large_objects(mask_slice, start_x=box['x1']+10, start_y=box['y1']+10)

    def ungroup_buttons(self, mask, start_x, start_y, box):
        h, w = mask.shape[:2]
        c_x = w // 2
        last_y = 0
        for y in range(h):
            if mask[y][c_x:].mean() <= 5:
                self.objects.append({'x1': start_x, 'y1': start_y + last_y, 'x2': start_x + w, 'y2': start_y + y,
                                     'height': y - last_y, 'width': w})
                last_y = y
        if last_y > 0:
            self.objects.append({'x1': start_x, 'y1': start_y + last_y, 'x2': start_x + w, 'y2': start_y + h,
                                 'height': h - last_y, 'width': w})
            self.objects.remove(box)

    def ungroup_buttons_(self, image, start_x, start_y):
        h, w = image.shape[:2]
        c_x = w // 2
        last_y = 0
        for y in range(h):
            if image[y][c_x:].mean() <= 5:
                self.objects.append({'x1': start_x, 'y1': start_y + last_y, 'x2': start_x + w, 'y2': start_y + y,
                                     'height': y - last_y, 'width': w})
                last_y = y
        if last_y > 0:
            self.objects.append({'x1': start_x, 'y1': start_y + last_y, 'x2': start_x + w, 'y2': start_y + h,
                                 'height': h - last_y, 'width': w})

    def draw_boxes(self, image):
        for box in self.objects:
            cv2.rectangle(image, (box['x1'], box['y1']), (box['x2'], box['y2']), (255, 0, 0), self.line_thickness)

    def find_horizontal_lines(self, mask):
        self.lines = []
        self.height = mask.shape[0] - 1
        self.lines.append(0)
        for y in range(self.height):
            if abs((mask[y, :, 0].mean() / 255) - (mask[y + 1, :, 0].mean() / 255)) > 0.1:
                self.lines.append(y)
        if mask[-1].mean() / 255 < 0.6:
            self.lines.append(self.height)

    def find_vertical_lines(self, mask):
        self.lines_dict = {}
        self.width = mask.shape[1] - 1
        lines_amount = len(self.lines) - 1
        for line_index in range(lines_amount):
            top_line, bottom_line = self.lines[line_index], self.lines[line_index + 1]
            image_slice = mask[top_line: bottom_line, :, 0]
            dict_key = f'{top_line}-{bottom_line}'
            self.lines_dict[dict_key] = []
            for x in range(image_slice.shape[1] - 2):
                if abs((image_slice[:, x].mean() / 255) - (image_slice[:, x + 1].mean() / 255)) > 0.3:
                    self.lines_dict[dict_key].append(x)
            if len(self.lines_dict[dict_key]) > 0:
                if len(self.lines_dict[dict_key]) % 2 != 0:
                    self.lines_dict[dict_key].append(self.width)
            else:
                self.lines_dict.pop(dict_key)

    def clean_objects(self):
        box_to_remove = []
        for box in self.objects:
            if box['y2'] - box['y1'] < self.min_height:
                box_to_remove.append(box)
            elif box['x2'] - box['x1'] < self.min_width:
                box_to_remove.append(box)

        for box in box_to_remove:
            self.objects.remove(box)


def combine_text_with_objects(objects, text, parent, image_num, padding=10, padding_y=20,
                              main_buttons=('wallet', 'market', 'card', 'settings')):
    text_dataframe = pd.DataFrame(text)
    indexes, result = [], []
    for obj in objects:
        x1, x2, y1, y2 = obj['x1'], obj['x2'], obj['y1'], obj['y2']
        text_in_objects = text_dataframe[['x1', 'y1', 'x2', 'y2', 'text']].where(
            (text_dataframe['x1'] > x1 - padding) &
            (text_dataframe['x2'] < x2 + padding) &
            (text_dataframe['y1'] < y2 + padding_y) &
            (text_dataframe['y2'] > y1 - padding)).dropna()
        result.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'text': [], 'type': 'object'})
        dicts_to_add = []
        for index, values in zip(text_in_objects.index, text_in_objects.values):
            x1, y1, x2, y2, text = values
            if any([SequenceMatcher(a=text, b=button).ratio() >= 0.75
                    for button in main_buttons]):
                continue
            indexes.append(index)
            dicts_to_add.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'text': text})
        result[-1]['text'] = dicts_to_add
    text_dataframe.drop(indexes, inplace=True)

    for text_row in text_dataframe.values:
        x1, y1, x2, y2, text = text_row[:5]
        result.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'text': text, 'type': 'text'})
        if any([SequenceMatcher(a=text, b=button).ratio() >= 0.75 for button in main_buttons]):
            result[-1]['analyzed'] = True
            result[-1]['clickable'] = True

    for element_id, item in enumerate(result):
        item['parent'] = parent
        item['image_id'] = image_num
        item['element_id'] = element_id
        item['action'] = 'No action'
        if 'analyzed' not in item.keys():
            item['analyzed'] = False
            item['clickable'] = False

    return result
