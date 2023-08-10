import logging
from scanner.navigation.essentials import move_mouse
from ..tools.image_similarity import check_similarity
from ..object_searcher.create_mask import create_mask


def check_for_changed_page(self, base_image, current_image):
    base_mask = create_mask(base_image)
    current_mask = create_mask(current_image)
    if check_similarity(self, base_mask, current_mask, confidence_coefficient=0.1, reduce_quality=False):
        return True
    return False


def process_changed_page(self, y1, y2, elements_on_page):
    elements_on_row = elements_on_page.where(
        (elements_on_page['y1'] >= y1 - self.textSearcher.text_box_reduction_coefficient_y) &
        (elements_on_page['y2'] <= y2 + self.textSearcher.text_box_reduction_coefficient_y)
    ).dropna().sort_values('x1')
    x1, y1, x2, y2 = elements_on_row.values[0][:4]
    move_mouse(self, rel_x1=x1, rel_y1=y1, rel_x2=x2, rel_y2=y2, click=True, sleep_time=self.loading_time, sleep=True)
