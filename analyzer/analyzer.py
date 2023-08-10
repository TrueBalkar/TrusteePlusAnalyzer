import pandas as pd
import numpy as np
import cv2
import os
import psutil
from difflib import SequenceMatcher
import re
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import shutil
from copy import copy
from configs import *

num_cores = os.cpu_count()
process = psutil.Process()
process.cpu_affinity([9])


result_path = CONFIGS['Analyzer']['ResultPath']
reference_app_path = CONFIGS['Analyzer']['ReferenceAppTemplatePath']
new_app_path = CONFIGS['Analyzer']['NewAppTemplatePath']
confidence_coefficient = CONFIGS['Analyzer']['ConfidenceCoefficient']
coin_dict = CONFIGS['Analyzer']['CoinDict']
action_dict = CONFIGS['Analyzer']['ActionDict']
base_regex = CONFIGS['Analyzer']['Regex']


def clean_string(string, regex=fr'{base_regex}'):
    return re.sub(regex, '', string)


def draw_boxes(x1, y1, x2, y2, image):
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 1)


def write_report_(true_path, ref_data, new_app_data, original_image, reference_original_image_path,
                  new_app_original_image_path, named_dir):
    path = original_image.split('/')
    image_name, extension = os.path.splitext(path.pop(-1))
    image_name = image_name.replace('_original', '')
    json_file = original_image.replace('_original.png', '.json')
    path = named_dir[json_file].split('/')
    true_path = true_path.split('/')
    index = 1
    new_path = copy(path)
    for new_app_original_path_part, ref_original_path_part in zip(reversed(json_file.split('/')[:-1]),
                                                                  reversed(true_path[:-1])):
        index += 1
        if ':' in new_app_original_path_part or new_app_original_path_part == 'swap':
            new_path[-index] = (f'{new_path[-index]}_({ref_original_path_part}_ref)='
                                f'({new_app_original_path_part}_new_app)')
        else:
            break
    path = '/'.join(new_path) + f'{true_path[-1]}'
    if os.path.exists(f'{result_path}{path.replace(".json", "_new_app.png")}'):
        new_app_original_image = cv2.imread(f'{result_path}{path.replace(".json", "_new_app.png")}')
    else:
        new_app_original_image = cv2.imread(f'{new_app_original_image_path}')
    if os.path.exists(f'{result_path}{path.replace(".json", "_reference.png")}'):
        reference_original_image = cv2.imread(f'{result_path}{path.replace(".json", "_reference.png")}')
    else:
        reference_original_image = cv2.imread(f'{reference_original_image_path}')

    print(f'{result_path}{path.replace(".json", ".txt")}')
    if not os.path.exists(f'{result_path}{path.replace(".json", ".txt")}'):
        if not os.path.exists(f'{result_path}{"/".join(path.split("/")[:-1])}'):
            os.makedirs(f'{result_path}{"/".join(path.split("/")[:-1])}')
        file = open(f'{result_path}{path.replace(".json", ".txt")}', 'w')
    else:
        file = open(f'{result_path}{path.replace(".json", ".txt")}', 'a')

    file.writelines(f'Ref data:\n')
    for values in ref_data:
        x1 = values['x1']
        y1 = values['y1']
        x2 = values['x2']
        y2 = values['y2']
        file.writelines(f'x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}\n')
        draw_boxes(x1, y1, x2, y2, reference_original_image)

    file.writelines(f'New app data:\n')
    for values in new_app_data:
        x1 = values['x1']
        y1 = values['y1']
        x2 = values['x2']
        y2 = values['y2']
        file.writelines(f'x1: {x1}, y1: {y1}, x2: {x2}, y2: {y2}\n')
        draw_boxes(x1, y1, x2, y2, new_app_original_image)

    print(path.replace(new_app_path, result_path))
    cv2.imwrite(f'{result_path}{path.replace(".json", "_new_app.png")}', new_app_original_image)
    cv2.imwrite(f'{result_path}{path.replace(".json", "_reference.png")}', reference_original_image)
    print(f'Found differences at: {path}{image_name}{extension}!')


def compare_coordinates(cords_1, cords_2):
    if any(abs(np.array(cords_1) - np.array(cords_2)) > 10):
        return False
    return True


def compare_details(json_file, original_image, named_1, named_2):
    file_name = json_file.split('/')[-1].split('.')[0]
    true_path = named_1[named_2[json_file]]
    if 'wallet/1:9' in json_file:
        print(f'TRUE TETHER PATH: {true_path}, {named_2[json_file]}, {json_file}')
    if isinstance(true_path, list):
        most_similar_path = str(true_path[0])
        similarity_score = 999
        current_file_name = int(file_name)
        for path in true_path:
            available_file_name = int(path.split('/')[-1].split('.')[0])
            available_similarity_score = abs(current_file_name - available_file_name) * 10
            for split_path, current_split_path in zip(reversed(path.split('/')[:-1]),
                                                      reversed(json_file.split('/')[:-1])):
                if ':' in current_split_path:
                    current_image_id, current_element_id = [int(split) for split in current_split_path.split(':')]
                else:
                    current_image_id, current_element_id = 0, 0
                if ':' in split_path:
                    available_image_id, available_element_id = [int(split) for split in split_path.split(':')]
                else:
                    available_image_id, available_element_id = 0, 0
                available_similarity_score += ((abs(current_image_id - available_image_id) * 5) +
                                               abs(current_element_id - available_element_id))
            else:
                if available_similarity_score < similarity_score:
                    similarity_score = int(available_similarity_score)
                    most_similar_path = path
        else:
            true_path = str(most_similar_path)
    new_app_original_image_path = f'{true_path.replace(".json", "_original.png")}'
    reference_original_image = f'{original_image}'
    new_app_json_file = pd.read_json(f'{true_path}')
    reference_json_file = pd.read_json(f'{json_file}')
    ref_data = []
    new_app_data = []
    for ref_values in reference_json_file.values[:5]:
        x1, y1, x2, y2, text = ref_values[:5]
        for new_app_values in new_app_json_file.values[:5]:
            new_x1, new_y1, new_x2, new_y2, new_text = new_app_values[:5]
            if abs(x1 - new_x1) <= 10 and abs(y1 - new_y1) <= 10 and abs(x2 - new_x2) <= 10 and abs(y2 - new_y2) <= 10:
                if type(text) == type(new_text):
                    if isinstance(text, list):
                        for words in text:
                            w_x1, w_y1, w_x2, w_y2 = words['x1'], words['y1'], words['x2'], words['y2']
                            if not any([abs(w_x1 - n_words['x1']) <= 10 and
                                        abs(w_y1 - n_words['y1']) <= 10 and
                                        abs(w_x2 - n_words['x2']) <= 10 and
                                        abs(w_y2 - n_words['y2']) <= 10 for n_words in new_text]):
                                ref_data.append({'x1': w_x1,
                                                 'y1': w_y1,
                                                 'x2': w_x2,
                                                 'y2': w_y2})
                break
        else:
            ref_data.append({'x1': x1,
                             'y1': y1,
                             'x2': x2,
                             'y2': y2})

    for new_app_values in new_app_json_file.values[:5]:
        x1, y1, x2, y2, text = new_app_values[:5]
        for ref_values in reference_json_file.values[:5]:
            ref_x1, ref_y1, ref_x2, ref_y2, ref_text = ref_values[:5]
            if abs(x1 - ref_x1) <= 10 and abs(y1 - ref_y1) <= 10 and abs(x2 - ref_x2) <= 10 and abs(y2 - ref_y2) <= 10:
                if type(text) == type(ref_text):
                    if isinstance(text, list):
                        for words in text:
                            w_x1, w_y1, w_x2, w_y2 = words['x1'], words['y1'], words['x2'], words['y2']
                            if not any([abs(w_x1 - n_words['x1']) <= 10 and
                                        abs(w_y1 - n_words['y1']) <= 10 and
                                        abs(w_x2 - n_words['x2']) <= 10 and
                                        abs(w_y2 - n_words['y2']) <= 10 for n_words in ref_text]):
                                new_app_data.append({'x1': w_x1,
                                                     'y1': w_y1,
                                                     'x2': w_x2,
                                                     'y2': w_y2})
                break
        else:
            new_app_data.append({'x1': x1,
                                 'y1': y1,
                                 'x2': x2,
                                 'y2': y2})

    if len(ref_data) > 0 or len(new_app_data) > 0:
        write_report_(true_path, ref_data, new_app_data, original_image, reference_original_image,
                      new_app_original_image_path, named_2)


def get_directories(path):
    files = sorted(os.listdir(path))
    dirs = []
    json_files = []
    original_images = []
    for filename in files:
        file_path = f'{path}/{filename}'
        if os.path.isdir(file_path):
            dirs.append(file_path)
        elif '_mask' in filename:
            json_files.append(file_path.replace('_mask.png', '.json'))
            original_images.append(file_path.replace('_mask.png', '_original.png'))
    return json_files, original_images, dirs


def name_path(path):
    split_path = path.split('/')[:-1]
    path_part = split_path.pop(-1)
    new_path = ''
    while ':' in path_part or path_part == 'swap':
        if path_part == 'swap':
            new_path = f'swapped/{new_path}'
            path_part = split_path.pop(-1)
            continue
        image_id, element_id = [int(part) for part in path_part.split(':')]
        json_path = f'{"/".join(split_path)}/{image_id}.json'
        df = pd.read_json(json_path)
        text = df.where(df['element_id'] == element_id).dropna().values[0]
        x1, y1, x2, y2 = text[:4]
        text = text[4]
        if isinstance(text, list):
            if text:
                text = word_tokenize(re.sub(r'\s\d|\d\s|\d', '', ' '.join([word['text'] for word in text])))
                if text:
                    text = select_text(pos_tag(text), new_path)
            else:
                new_text = df.where((df['type'] == 'text') &
                                    (df['x1'] >= x2 - 5) &
                                    (df['y1'] >= y1 - 5) &
                                    (df['y2'] <= y2 + 5)).dropna()
                if len(new_text) > 0:
                    text = word_tokenize(re.sub(r'\s\d|\d\s|\d', '', new_text['text'].iloc[0]))
                    if text:
                        text = select_text(pos_tag(text), new_path)
                else:
                    json_path = f'{"/".join(split_path)}/{path_part}/1.json'
                    if os.path.exists(json_path):
                        df = pd.read_json(json_path)
                        text = df.where(df['type'] == 'text').dropna()['text'].iloc[0]
                        if text.replace(' ', '') != '':
                            text = word_tokenize(re.sub(r'\s\d|\d\s|\d', '', text))
                            if text:
                                text = select_text(pos_tag(text), new_path)
                            else:
                                text = 'NO_TEXT'
                        else:
                            text = 'NO_TEXT'
                    else:
                        text = 'NO_TEXT'
        else:
            text = word_tokenize(re.sub(r'\s\d|\d\s|\d', '', text))
            if text:
                text = select_text(pos_tag(text), new_path)
                if text.replace(' ', '') == '':
                    text = 'NO_TEXT'
            else:
                text = 'NO_TEXT'
        # new_path = f'{text}_({path_part})/{new_path}'
        new_path = f'{text}/{new_path}'
        path_part = split_path.pop(-1)
    new_path = f'{path_part}/{new_path}'
    print(f'{path}: {new_path}')
    return new_path


def select_text(text, prev_path):
    path = prev_path.split('/')
    words_to_send = []
    words, tags = [], []
    blacklist = ['nan', 'mna', 'os', 'o', 's', 'olsh', 'us', 'wamwsin', 'sse', 'so', 'hrmw', 'mmhrsng', 'amim', 'mson',
                 'hnsaw', 'fee', 'crn']
    for word, tag in text:
        if word[-1] == 's':
            word = word[:-1]
        words.append(word.replace('sk', '').replace('sx', '').replace('sr', ''))
        tags.append(tag)
    print(words, tags)
    for action in action_dict.keys():
        if action in words:
            return action_dict[action]
    for word in words:
        if word in coin_dict.keys():
            return coin_dict[word]
        elif word in coin_dict.values():
            return word
    # print(words, tags)
    if 'NNS' in tags or 'NNP' in tags or 'VBZ' in tags or 'FW' in tags or 'IN' in tags:
        for word, tag in zip(words, tags):
            if tag in ['NNS', 'NNP', 'VBZ', 'FW', 'IN'] and word not in blacklist:
                if word in coin_dict.keys():
                    word = coin_dict[word]
                return word
    if 'VB' in tags and 'RP' in tags:
        for word, tag in zip(words, tags):
            if tag == 'VB' or tag == 'RP':
                words_to_send.append(word)
            if len(words_to_send) == 2:
                return '_'.join(words_to_send)
    if len(words_to_send) == 1:
        return words_to_send[0]
    if 'TO' in tags and 'DT' in tags:
        for word, tag in zip(words, tags):
            if len(words_to_send) == 2:
                if tag == 'NN':
                    words_to_send.append(word)
                return '_'.join(words_to_send)
            elif tag == 'TO' or tag == 'DT':
                words_to_send.append(word)
    if len(words_to_send) == 1:
        return words_to_send[0]
    if 'JJ' in tags:
        for word, tag in zip(words, tags):
            if tag == 'JJ' and word not in blacklist:
                if word in coin_dict.keys():
                    word = coin_dict[word]
                return word
    largest_word = ''
    for word, tag in zip(words, tags):
        if word not in blacklist:
            if tag == 'NN' and len(word) > len(largest_word):
                largest_word = str(word)
            elif tag == 'NN' and len(word) == len(largest_word):
                mean_ratio_prev, mean_ratio_current = [], []
                for path_part in path:
                    mean_ratio_prev.append(SequenceMatcher(a=word, b=path_part).ratio())
                    mean_ratio_current.append(SequenceMatcher(a=word, b=path_part).ratio())
                mean_ratio_prev = sum(mean_ratio_prev) / len(mean_ratio_prev)
                mean_ratio_current = sum(mean_ratio_current) / len(mean_ratio_current)
                # print('RATIO', mean_ratio_prev, mean_ratio_current, word, largest_word, path)
                if mean_ratio_prev < mean_ratio_current:
                    largest_word = str(word)
    if largest_word in coin_dict.keys():
        largest_word = coin_dict[largest_word]
    return largest_word if largest_word != '' else 'NO_TEXT'


def write_missing_page(missing_page, named_dir):
    clean_path = missing_page.split('/')
    base_path = clean_path[1]
    file_name = clean_path[-1].split('.')[0] + '_original.png'
    new_path = named_dir[missing_page].split('/')
    index = 1
    for original_path_part in reversed(clean_path[:-1]):
        index += 1
        if ':' in original_path_part or original_path_part == 'swap':
            new_path[-index] = f'{new_path[-index]}_({original_path_part})'
        else:
            break
    new_path = '/'.join(new_path)
    clean_path = '/'.join(clean_path[:-1]) + '/' + file_name
    if not os.path.exists(f'{result_path}not_found/{base_path}/{new_path}'):
        os.makedirs(f'{result_path}not_found/{base_path}/{new_path}')
    shutil.copyfile(f'{clean_path}',
                    f'{result_path}not_found/{base_path}/{new_path}/{file_name}')
    print(f'{named_dir[missing_page]} not found!')


analyzed_files = []
named_dirs_new = {}
named_dirs_ref = {}

new_json, new_images, new_directories = get_directories(new_app_path)
ref_json, ref_images, ref_directories = get_directories(reference_app_path)
named_files = []
while True:
    buffer_directories = list(new_directories)
    current_new_level = {}
    for directory_new in buffer_directories:
        new_json, new_images, buffer = get_directories(directory_new)
        for buff in buffer:
            new_directories.append(buff)
        for j, i in zip(new_json, new_images):
            new_name = name_path(j)
            named_dirs_new[j] = new_name
            if new_name not in named_dirs_new.keys():
                named_dirs_new[new_name] = j
            else:
                if isinstance(named_dirs_new[new_name], str):
                    named_dirs_new[new_name] = [named_dirs_new[new_name]]
                named_dirs_new[new_name].append(j)
        new_directories.pop(0)

    buffer_directories = list(ref_directories)
    current_ref_level = {}
    for directory_ref in buffer_directories:
        ref_json, ref_images, buffer = get_directories(directory_ref)
        for buff in buffer:
            ref_directories.append(buff)
        for j, i in zip(ref_json, ref_images):
            # print(j)
            if j not in named_files:
                named_files.append(j)
            else:
                continue
            new_name = name_path(j)
            named_dirs_ref[j] = new_name
            if new_name not in named_dirs_ref.keys():
                named_dirs_ref[new_name] = j
            else:
                if isinstance(named_dirs_ref[new_name], str):
                    named_dirs_ref[new_name] = [named_dirs_ref[new_name]]
                named_dirs_ref[new_name].append(j)
        ref_directories.pop(0)

    if len(new_directories) == 0 and len(ref_directories) == 0:
        break

ref_json, ref_images, ref_directories = get_directories(reference_app_path)
new_json, new_images, new_directories = get_directories(new_app_path)
while True:
    buffer_directories = list(ref_directories)
    for directory in buffer_directories:
        json, images, buffer = get_directories(directory)
        for buff in buffer:
            ref_directories.append(buff)
        for j, i in zip(json, images):
            if j not in analyzed_files:
                analyzed_files.append(j)
            else:
                continue
            if named_dirs_ref[j] in named_dirs_new.keys():
                compare_details(j, i, named_dirs_new, named_dirs_ref)
            else:
                write_missing_page(j, named_dirs_ref)
        ref_directories.pop(0)

    buffer_directories = list(new_directories)
    for directory in buffer_directories:
        json, images, buffer = get_directories(directory)
        for buff in buffer:
            new_directories.append(buff)
        for j, i in zip(json, images):
            if j not in analyzed_files:
                analyzed_files.append(j)
            else:
                continue
            if named_dirs_new[j] in named_dirs_ref.keys():
                compare_details(j, i, named_dirs_ref, named_dirs_new)
            else:
                write_missing_page(j, named_dirs_new)
        new_directories.pop(0)
    if len(ref_directories) == 0 and len(new_directories) == 0:
        break
