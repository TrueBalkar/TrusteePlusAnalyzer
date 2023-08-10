from ..tools.image_similarity import check_similarity
from ..navigation.essentials import move_mouse, scroll
from ..triggers.opened_browser import check_for_opened_browser
import logging
import pyautogui
import time
import numpy as np


def make_screenshots(self, page_name):
    move_mouse(self, rel_x1=self.width // 2, rel_y1=self.height // 2)
    self.screenshotMaker.make_screenshot()
    image_id = 1
    current_image = self.screenshotMaker.image
    prev_image = np.zeros(current_image.shape, dtype='uint8')
    while not check_similarity(self, prev_image, current_image) and image_id <= self.max_page_len:
        prev_image = np.array(current_image)
        if check_for_opened_browser(self, prev_image):
            logging.info(f"Page {page_name} triggered opening of the browser!~yellow")
            self.blacklisted_pages.append(page_name)
            break
        self.images.append((np.array(prev_image), page_name, image_id))
        if image_id == 1:
            move_mouse(self, self.width // 2, int(self.height * self.scroll_up_mouse_pos))
            pyautogui.dragTo(0, int(self.height * self.scroll_down_mouse_pos), self.scroll_time)
            self.screenshotMaker.make_screenshot()
            if check_similarity(self, prev_image, self.screenshotMaker.image):
                image_id += 1
                break
            move_mouse(self, self.width // 2, int(self.height * self.scroll_up_mouse_pos))
            pyautogui.dragTo(0, int(self.height * self.scroll_down_mouse_pos), self.scroll_time)
            time.sleep(self.scroll_time)
        else:
            scroll(self)
        self.screenshotMaker.make_screenshot()
        current_image = np.array(self.screenshotMaker.image)
        image_id += 1
    logging.info(f'Page: {page_name} consists of {image_id - 1} images.~cyan')
    if page_name in self.main_buttons.keys():
        move_mouse(self, self.width // 2, self.height // 2)
        pyautogui.scroll(1)
        time.sleep(self.scroll_time)
