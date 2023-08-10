import pyautogui
import time
import logging
from difflib import SequenceMatcher
from scanner.navigation.essentials import move_mouse


def open_app(self):
    self.screenshotMaker.make_screenshot()
    self.main_screen = self.screenshotMaker.image
    self.read_text(self.main_screen, empty_results=False)
    ratio = (len(self.app_name) - 1) / int(len(self.app_name) * 1.3)
    logging.info(f'Opening program {self.app_name}...~green')
    for values in self.textSearcher.text:
        if SequenceMatcher(a=self.app_name.lower(), b=values['text']).ratio() >= ratio:
            self.app_coordinates['x'] = values['x1'] + ((values['x2'] - values['x1']) // 2)
            self.app_coordinates['y'] = values['y1'] + ((values['y2'] - values['y1']) // 2)
            move_mouse(self, rel_x1=self.app_coordinates['x'], rel_y1=self.app_coordinates['y'],
                       click=True)
            logging.info(f'Waiting for program {self.app_name} to open...~green')
            for seconds in range(int(self.loading_time * 10), 0, -1):
                logging.info(f'Time till analyzer start: {seconds} seconds(s)!~green')
                time.sleep(1)
            logging.info(f'Analyzer started!~green')
            self.textSearcher.empty_prediction_results()
            move_mouse(self, rel_x1=self.width // 2, rel_y1=self.height // 2)
            pyautogui.scroll(1)
            time.sleep(self.scroll_time)
            break


def open_browser(self):
    browser_name = 'Chrome'
    self.screenshotMaker.make_screenshot()
    self.main_screen = self.screenshotMaker.image
    self.read_text(self.main_screen, empty_results=False)
    ratio = (len(browser_name) - 1) / int(len(browser_name) * 1.3)
    logging.info(f'Opening browser {browser_name}...~green')
    for values in self.textSearcher.text:
        if SequenceMatcher(a=browser_name.lower(), b=values['text']).ratio() >= ratio:
            self.app_coordinates['x'] = values['x1'] + ((values['x2'] - values['x1']) // 2)
            self.app_coordinates['y'] = values['y1'] + ((values['y2'] - values['y1']) // 2)
            move_mouse(self, rel_x1=self.app_coordinates['x'], rel_y1=self.app_coordinates['y'],
                       click=True)
            logging.info(f'Waiting for program {browser_name} to open...~green')
            for seconds in range(int(self.loading_time * 10), 0, -1):
                logging.info(f'Waiting for browser to start: {seconds} seconds(s)!~green')
                time.sleep(1)
            logging.info(f'Browser started!~green')
            self.textSearcher.empty_prediction_results()
            pyautogui.hotkey('ctrl', 'h')
            time.sleep(self.loading_time * 2)
            break
