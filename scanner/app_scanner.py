import threading
import pandas as pd
import numpy as np
import time
import logging
from copy import copy
from configs import *
from image_loader.image_loader import ScreenshotMaker
from .text_searcher.text_search import TextSearcher
from .object_searcher.object_search import combine_text_with_objects, ObjectSearcher
from .object_searcher.create_mask import create_mask
from .navigation.navigator import step_back
from .navigation.essentials import move_mouse
from .triggers.returned_to_base_images import check_if_returned_to_base_images
from .tools.blacklist_processor import check_if_blacklisted, check_for_blacklisted_page, check_for_blacklisted_element
from .tools.action_processor import process_action
from .app_loader.app_loader import open_app, open_browser
from .tools.make_screenshots import make_screenshots
from .tools.file_writer import write_image, write_json
from .tools.queue_manager import get_next_item_from_queue
from .tools.essentials import (page_depth_exceeds_limit, handle_swap_page, adjust_scroll_position,
                               navigate_and_handle_errors, check_if_scanning_finished, interact_and_verify_action,
                               check_for_already_existing_page, check_for_wrong_action_report)


class AppScanner:
    def __init__(self, settings=CONFIGS):
        self.app_name = settings['Main']['AppName']
        self.template_path = settings['Main']['TemplatePath']
        self.main_app_screen_page = settings['Main']['MainAppScreenPage']
        self.run = True
        self.status = 'Dead'
        self.main_screen = None
        self.textSearcher = TextSearcher()
        self.objectSearcher = ObjectSearcher()
        self.screenshotMaker = ScreenshotMaker()
        self.start_x = copy(self.screenshotMaker.region[0])
        self.start_y = copy(self.screenshotMaker.region[1])
        self.width = copy(self.screenshotMaker.region[2])
        self.height = copy(self.screenshotMaker.region[3])
        self.app_coordinates = {'x': 0, 'y': 0}
        self.main_pages = []
        self.main_buttons = {}
        self.wallet_image = None
        self.similarity_confidence_coefficient = settings['Main']['SimilarityConfidenceCoefficient']
        self.loading_time = settings['Timeouts']['LoadingTimeout']
        self.scroll_time = settings['Timeouts']['ScrollingTimeout']
        self.go_back_time = settings['Timeouts']['StepBackTimeout']
        self.scroll_distance = settings['Navigation']['ScrollDistance']
        self.max_depth = settings['Navigation']['MaxDepth']
        self.blacklist = settings['Blacklist']['BlacklistedWords']
        self.blacklisted_pages = settings['Blacklist']['BlacklistedPages']
        self.nav_pages = settings['Navigation']['NavPages']
        self.nav_scan_pages = settings['Navigation']['ScanPages']
        self.max_page_len = settings['Navigation']['MaxPageLength']
        self.scroll_up_mouse_pos = 0.5 + (self.scroll_distance / 2) / 2
        self.scroll_down_mouse_pos = 0.5 - (self.scroll_distance / 2) / 2
        self.tether_coord = {'x1': None, 'y1': None, 'x2': None, 'y2': None}
        self.scrolls = 1
        self.swap = []
        self.images = []
        self.data_queue = []
        self.current_position = []
        self.base_images = {}

    def prepare_apps(self):
        open_browser(self)
        open_app(self)

    def start_scanner(self):
        logging.info(f'|n|Current settings:|n|'
                     f'App name: {self.app_name};|n|'
                     f'Template path: {self.template_path};|n|'
                     f'Similarity confidence coefficient: {self.similarity_confidence_coefficient};|n|'
                     f'Blacklisted pages: {self.blacklisted_pages};|n|'
                     f'Blacklisted elements: {self.blacklist};|n|'
                     f'Scroll distance: {self.scroll_distance};|n|'
                     f'Scrolling timeout: {self.scroll_time} sec(s);|n|'
                     f'Go back timeout: {self.go_back_time} sec(s);|n|'
                     f'Loading timeout: {self.loading_time} sec(s);~gray')
        logging.info('Scanner is starting...~green')
        logging.info('Main process started...~green')
        thread = threading.Thread(target=self.main)
        thread.start()
        # try:
        logging.info('Image reader started...~green')
        self.read_image_details()
        # except Exception as Argument:
        #     logging.error('Something went wrong at image details reader, and it stopped working...~red')
        #     logging.error(f'Error message:|n|{Argument}~red')

    def write_json(self, template):
        template.to_json(self.template_path + 'templates.json')

    def main(self):
        self.write_main_pages_details()
        page_name = copy(self.main_app_screen_page)
        images = {}
        while True:
            if len(self.data_queue) > 0:
                data = get_next_item_from_queue(self, page_name)
                if page_name != data['parent'].values[0]:
                    images = {}
                page_name = data['parent'].values[0]
                if page_depth_exceeds_limit(self, page_name):
                    continue
                image_id = data['image_id'].iloc[0]
                if check_for_blacklisted_page(self, data):
                    continue
                if handle_swap_page(self, page_name, data):
                    continue
                adjust_scroll_position(self, image_id)
                if navigate_and_handle_errors(self, page_name, data):
                    continue
                self.screenshotMaker.make_screenshot()
                self.base_images['-'.join(self.current_position)] = self.screenshotMaker.image
                logging.info(f'Making screenshots on page: {page_name}, image_id: {image_id}~pink')
                self.get_image_details(data, page_name, images)
            elif self.status == 'Dead':
                if check_if_scanning_finished(self):
                    return 'Analysis finished'
        # except Exception as Argument:
        #     logging.error('Something went wrong at app navigator,and it stopped working...~red')
        #     logging.error(f'Error message:|n|{Argument}~red')

    def get_image_details(self, data, parent, images):
        skip_objects = False
        for text in data['text']:
            if check_if_blacklisted(self, text, ['transfer type']):
                skip_objects = True
        analyzed_page_part = []
        for element in data.values:
            if skip_objects:
                if element[5] == 'object':
                    continue
            x1, y1, x2, y2 = element[:4]
            analyzed_element = {'text': element[4], 'type': element[5], 'image_id': element[7],
                                'element_id': element[8], 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                'parent': parent, 'action': None, 'analyzed': True, 'clickable': None}
            if check_for_blacklisted_element(self, analyzed_element):
                analyzed_element['clickable'] = False
                analyzed_element['action'] = 'blacklisted'
                continue
            status = interact_and_verify_action(self, x1, y1, x2, y2)
            analyzed_element['clickable'] = False if status == 'No action' else True
            analyzed_element['action'] = status
            element_parent_name = f'{parent}-{element[7]}:{element[8]}'
            logging.info(f'Element {element_parent_name} triggered following action: {status}~pink')
            if status == 'New page':
                send_info = check_for_already_existing_page(self, images, element_parent_name)
                if send_info:
                    images[element_parent_name] = self.screenshotMaker.image
            else:
                send_info = True
            process_action(self, status, x1, y1, x2, y2, data, element_parent_name, send_info=send_info)
            if check_if_returned_to_base_images(self):
                check_for_wrong_action_report(self, parent, status, element_parent_name)
            else:
                if status not in ['Changed current page', 'No action']:
                    step_back(self)
            analyzed_page_part.append(analyzed_element)

    def read_image_details(self):
        while self.run is True:
            if len(self.images) > 0:
                self.status = 'Alive'
                current_image, page_name, image_id = self.images.pop(0)
                # logging.info(f'Writing details of image: {image_id} on page: {page_name}...~purple')
                write_image(self, path=page_name, image_name=str(image_id)+'_original', image=current_image)
                final_image = copy(current_image)
                current_mask = copy(current_image)
                # logging.info('Reading text...~purple')
                self.read_text(current_image, mask_image=current_mask, draw_boxes=False, empty_results=False)
                # logging.info('Reading objects...~purple')
                self.read_objects(current_image, current_mask, draw_boxes=False, empty_results=False)
                for text in self.textSearcher.text:
                    if check_if_blacklisted(self, text, ['trusteenative isnt responding']):
                        logging.info(f'Due to page: {page_name} being "app not responding" menu, '
                                     f'it will be blacklisted and skipped!~yellow')
                        self.blacklisted_pages.append(page_name)
                if not self.textSearcher.text and not self.objectSearcher.objects:
                    self.textSearcher.empty_prediction_results()
                    self.objectSearcher.empty_objects_data()
                    self.status = 'Dead'
                    continue
                elif not self.textSearcher.text:
                    data = pd.DataFrame(self.objectSearcher.objects)
                    data['text'] = [[] for i in range(len(data))]
                    data['type'] = 'object'
                    data['parent'] = page_name
                    data['image_id'] = image_id
                    data['element_id'] = [i for i in range(len(data))]
                    data['action'] = 'No action'
                    data['analyzed'] = False
                    data['clickable'] = False
                elif not self.objectSearcher.objects:
                    data = pd.DataFrame(self.textSearcher.text)
                    data['type'] = 'text'
                    data['parent'] = page_name
                    data['image_id'] = image_id
                    data['element_id'] = [i for i in range(len(data))]
                    data['action'] = 'No action'
                    data['analyzed'] = False
                    data['clickable'] = False
                else:
                    data = pd.DataFrame(combine_text_with_objects(self.objectSearcher.objects,
                                                                  self.textSearcher.text,
                                                                  page_name,
                                                                  image_id))
                data.sort_values('y1', inplace=True)
                current_mask = create_mask(current_mask, reduce_quality=False)
                self.textSearcher.draw_boxes(final_image)
                self.objectSearcher.draw_boxes(final_image)
                for swap in self.swap:
                    if swap in page_name:
                        self.blacklisted_pages.append(page_name)
                for text in data['text'].where(data['type'] == 'text').dropna():
                    if check_if_blacklisted(self, text, ['swap']):
                        self.swap.append(page_name)
                    if self.tether_coord['x1'] is None:
                        if check_if_blacklisted(self, text, ['select asset']):
                            object_df = data['text'].where(data['type'] == 'object').dropna()
                            for index, asset_text in zip(object_df.index, object_df):
                                if check_if_blacklisted(self, asset_text, ['tether', 'usdt',
                                                                           'tether usdt', 'usdt tether']):
                                    self.tether_coord['x1'] = data['x1'].loc[index]
                                    self.tether_coord['y1'] = data['y1'].loc[index]
                                    self.tether_coord['x2'] = data['x2'].loc[index]
                                    self.tether_coord['y2'] = data['y2'].loc[index]
                data.to_json(self.template_path + page_name.replace('-', '/') + '/' + str(image_id) + '.json')
                write_image(self, path=page_name, image_name=str(image_id) + '_mask', image=current_mask)
                write_image(self, path=page_name, image_name=str(image_id), image=final_image)
                # logging.info(f'Details of image: {image_id} on page: {page_name}. '
                # f'Has been written successfully!~purple')
                self.textSearcher.empty_prediction_results()
                self.objectSearcher.empty_objects_data()
                self.data_queue.append((data, page_name))
                self.status = 'Dead'
                logging.info(f'Amount of images in queue: {len(self.images)}~purple')
                logging.info(f'Amount of data in queue: {len(self.data_queue)}~purple')
            else:
                time.sleep(self.loading_time)

    def read_text(self, image, mask_image=None, refine_text=True, draw_boxes=True, empty_results=True):
        self.textSearcher.read_image(image)
        self.textSearcher.write_prediction_details()
        if self.textSearcher.text:
            if refine_text is True:
                self.textSearcher.refine_text()
                self.textSearcher.clean_big_text_boxes()
                # print(self.textSearcher.__dict__)
            if mask_image is not None:
                self.textSearcher.erase_text(mask_image)
            if draw_boxes is True:
                self.textSearcher.draw_boxes(image)
            if empty_results is True:
                self.textSearcher.empty_prediction_results()

    def read_objects(self, image, clean_image, draw_boxes=True, empty_results=True):
        mask_image = copy(clean_image)
        self.objectSearcher.image = clean_image
        mask_image = create_mask(mask_image, reduce_quality=False)
        self.objectSearcher.find_large_objects(mask_image)
        if self.objectSearcher.objects:
            self.objectSearcher.find_small_objects()
            self.objectSearcher.clean_objects()
            if draw_boxes:
                self.objectSearcher.draw_boxes(image)
            if empty_results:
                self.objectSearcher.empty_objects_data()

    def find_main_pages_buttons(self):
        self.screenshotMaker.make_screenshot()
        self.wallet_image = np.array(self.screenshotMaker.image)
        self.read_text(self.wallet_image, draw_boxes=False, empty_results=False)
        text = pd.DataFrame(self.textSearcher.text)
        self.textSearcher.empty_prediction_results()
        self.main_pages = []
        for values in text[['x1', 'y1', 'x2', 'y2', 'text']].values:
            for button_name in self.nav_scan_pages:
                if check_if_blacklisted(self, text=values[4], blacklist=[button_name]):
                    self.main_pages.append(values[:-1].tolist() + [button_name])

        max_colors = 0
        for button in self.main_pages:
            colors = len(np.unique(self.screenshotMaker.image[button[3]+15:, button[0]:button[2]].reshape(-1, 3),
                                   axis=0))
            if colors > max_colors:
                self.main_app_screen_page = button[4]
                max_colors = colors
        logging.info(f'Main app screen: {self.main_app_screen_page}~green')
        self.current_position.append(self.main_app_screen_page)

    def find_main_buttons(self):
        self.find_main_pages_buttons()
        for page in self.main_pages:
            self.main_buttons[page[4]] = [self.start_x + page[0] + (page[2] - page[0]) // 2,
                                          self.start_y + page[1] + (page[3] - page[1]) // 2]

    def write_main_pages_details(self):
        logging.info('Reading main pages details...~green')
        self.find_main_buttons()
        for page in self.main_pages:
            move_mouse(self, rel_x1=page[0], rel_y1=page[1], rel_x2=page[2], rel_y2=page[3],
                       sleep_time=self.loading_time * 2, click=True, sleep=True)
            make_screenshots(self, page[4])
            self.main_buttons[page[4]] = [self.start_x + page[0] + (page[2] - page[0]) // 2,
                                          self.start_y + page[1] + (page[3] - page[1]) // 2]

        move_mouse(self, rel_x1=self.main_pages[0][0], rel_y1=self.main_pages[0][1],
                   rel_x2=self.main_pages[0][2], rel_y2=self.main_pages[0][3],
                   sleep_time=self.loading_time * 2, click=True, sleep=True)
        # self.write_json()
