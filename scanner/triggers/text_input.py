import pyautogui
import time
from ..navigation.essentials import move_mouse
from ..navigation.navigator import step_back
from ..tools.image_similarity import check_similarity


def check_for_text_input(current_image):
    height, width = current_image.shape[:2]
    enter_place = current_image[int(height * 0.9):, int(width * 0.5):]
    if enter_place[:, :, 2].sum() > (enter_place[:, :, 1].sum() + enter_place[:, :, 0].sum()) * 0.55:
        return True
    return False


def process_text_input(self, x1, y1, x2, y2):
    self.screenshotMaker.make_screenshot()
    current_image = self.screenshotMaker.image
    pyautogui.press('enter')
    time.sleep(self.loading_time)
    self.screenshotMaker.make_screenshot()
    new_current_image = self.screenshotMaker.image
    counts = 0
    go_back = False
    while check_similarity(self, current_image, new_current_image):
        if go_back is True:
            step_back(self)
        if (counts // 3) * 3 == counts:
            move_mouse(self, rel_x1=x1, rel_y1=y1, rel_x2=x2, rel_y2=y2, click=True, sleep=True)
            go_back = True
        else:
            go_back = False
        time.sleep(self.loading_time)
        self.screenshotMaker.make_screenshot()
        new_current_image = self.screenshotMaker.image
        counts += 1
