import logging
import pyautogui
import time
import pandas as pd
from ..navigation.essentials import scroll, move_mouse
from ..navigation.navigator import navigate
from ..triggers.swap import process_swap
from ..tools.action_processor import check_action_kind
from .blacklist_processor import check_for_blacklisted_page
from ..tools.image_similarity import check_similarity


def page_depth_exceeds_limit(self, page_name):
    if len(page_name.split('-')) > self.max_depth:
        logging.info(f'Due to page {page_name} being deeper than max depth, it will be skipped!~yellow')
        return True
    return False


def adjust_scroll_position(self, image_id):
    if image_id > self.scrolls:
        scroll(self, image_id - self.scrolls)
        self.scrolls = int(image_id)
    elif image_id < self.scrolls:
        move_mouse(self, self.width // 2, self.height // 2)
        self.scrolls = 1
        pyautogui.scroll(1)
        time.sleep(self.loading_time)


def navigate_and_handle_errors(self, page_name, data):
    if navigate(self, path=page_name) == 'Error':
        if check_for_blacklisted_page(self, data):
            self.app_details = pd.concat([self.app_details, data], ignore_index=True)
        return True
    return False


def check_if_scanning_finished(self):
    for i in range(10):
        time.sleep(self.loading_time)
        if self.status == 'Alive':
            break
        if i == 9:
            if len(self.data_queue) == 0 and self.status == 'Dead':
                self.run = False
                return True
            else:
                break
    return False


def interact_and_verify_action(self, x1, y1, x2, y2):
    self.screenshotMaker.make_screenshot()
    current_image = self.screenshotMaker.image
    move_mouse(self, x1, y1, x2, y2, click=True, sleep=True, sleep_time=self.loading_time / 2)
    status = check_action_kind(self, current_image)
    if status == 'No action':
        move_mouse(self, x1, y1, x2, y2, click=True, sleep=True, sleep_time=self.loading_time / 2)
        status = check_action_kind(self, current_image)
        if status != 'No action':
            time.sleep(self.loading_time / 2)
            status = check_action_kind(self, current_image)
    else:
        time.sleep(self.loading_time / 2)
        status = check_action_kind(self, current_image)
    return status


def check_for_already_existing_page(self, images, element_parent_name):
    self.screenshotMaker.make_screenshot()
    for child, image in zip(images.keys(), images.values()):
        if check_similarity(self, image, self.screenshotMaker.image, confidence_coefficient=0.03):
            logging.info(f'Element {element_parent_name} triggered same action as {child}~pink')
            return False
    return True


def check_for_wrong_action_report(self, parent, status, element_parent_name):
    if '-'.join(self.current_position) != parent and status == 'New page':
        logging.info(f'Previous report about action trigger was wrong!~red')
        logging.info(f'Element {element_parent_name} triggered following action: Changed current page~pink')
        self.blacklisted_pages.append(element_parent_name)
        navigate(self, parent)
    elif '-'.join(self.current_position) != parent:
        logging.info(f'Current position: {parent} changed to '
                     f'{"-".join(self.current_position)}~yellow')
        navigate(self, parent)
        scroll(self, self.scrolls - 1)
