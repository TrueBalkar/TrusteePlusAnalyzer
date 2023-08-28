import numpy as np
from ..navigation.essentials import move_mouse
from ..object_searcher.create_mask import create_mask


def check_for_dropdown_menu(current_image):
    mask = create_mask(current_image)
    max_coverage = 0.05
    height, width = mask.shape[:2]
    for row_num, row in enumerate(mask[:-int(height * 0.2)]):
        if (row.sum() / 255) / width <= max_coverage:
            for i in range(int(height * 0.01)):
                if (mask[row_num + i].sum() / 255) / width <= max_coverage:
                    max_coverage = (mask[row_num + i].sum() / 255) / width
                else:
                    max_coverage = 0.05
                    break
            else:
                return True
    return False


def process_dropdown_menu(self, parent, screenshot=True):
    if screenshot is True:
        self.screenshotMaker.make_screenshot()
        self.images.append((np.array(self.screenshotMaker.image), parent, 1))
        self.blacklisted_pages.append(parent)
    move_mouse(self, rel_x1=self.width // 2, rel_y1=int(self.height * 0.05), click=True, sleep=True)
