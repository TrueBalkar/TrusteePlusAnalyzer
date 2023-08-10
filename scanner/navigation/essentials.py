import logging
import time
import pyautogui
from copy import copy


def go_back():
    pyautogui.hotkey('ctrl', 'backspace')


def scroll(self, amount=1):
    for i in range(amount):
        move_mouse(self, self.width // 2, int(self.height * self.scroll_up_mouse_pos))
        pyautogui.dragTo(0, int(self.height * self.scroll_down_mouse_pos), self.scroll_time)
        move_mouse(self, self.width // 2, int(self.height * self.scroll_up_mouse_pos))
        pyautogui.dragTo(0, int(self.height * self.scroll_down_mouse_pos), self.scroll_time)
        time.sleep(self.scroll_time)


def move_mouse(self, rel_x1, rel_y1, rel_x2=None, rel_y2=None, start_x=None, start_y=None, sleep_time=None,
               click=False, sleep=False):
    if start_x is None:
        start_x = copy(self.start_x)
    if start_y is None:
        start_y = copy(self.start_y)
    if sleep_time is None:
        sleep_time = copy(self.loading_time)
    if rel_x2 is None and rel_y2 is None:
        pyautogui.moveTo(start_x + rel_x1, start_y + rel_y1)
    elif rel_x2 is None:
        pyautogui.moveTo(start_x + rel_x1, start_y + rel_y1 + (rel_y2 - rel_y1) // 2)
    elif rel_y2 is None:
        pyautogui.moveTo(start_x + rel_x1 + (rel_x2 - rel_x1) // 2, start_y + rel_y1)
    else:
        pyautogui.moveTo(start_x + rel_x1 + (rel_x2 - rel_x1) // 2, start_y + rel_y1 + (rel_y2 - rel_y1) // 2)
    if click:
        pyautogui.click()
    if sleep:
        time.sleep(sleep_time)
