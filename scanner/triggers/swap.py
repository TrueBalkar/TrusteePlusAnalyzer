from ..navigation.essentials import move_mouse
from ..navigation.navigator import step_back
from ..tools.image_similarity import check_similarity
from ..tools.blacklist_processor import check_if_blacklisted
from ..tools.make_screenshots import make_screenshots


def process_swap(self, data, parent):
    for index, text in zip(data.index, data['text']):
        if check_if_blacklisted(self, text, ['select']):
            x1, y1, x2, y2 = data[['x1', 'y1', 'x2', 'y2']].loc[index]
            x1 = int(x1 + (x2 - x1) * 0.75)
            self.screenshotMaker.make_screenshot()
            current_image = self.screenshotMaker.image
            for count in range(10):
                if check_similarity(self, current_image, self.screenshotMaker.image):
                    move_mouse(self, rel_x1=x1, rel_y1=y1, rel_x2=x2, rel_y2=y2, click=True, sleep=True)
                    self.screenshotMaker.make_screenshot()
                else:
                    break
            else:
                break
            current_image = self.screenshotMaker.image
            for count in range(10):
                if check_similarity(self, current_image, self.screenshotMaker.image):
                    move_mouse(self, rel_x1=self.tether_coord['x1'], rel_y1=self.tether_coord['y1'],
                               rel_x2=self.tether_coord['x2'], rel_y2=self.tether_coord['y2'],
                               click=True, sleep=True)
                    self.screenshotMaker.make_screenshot()
                else:
                    break
            else:
                step_back(self)
                break
            make_screenshots(self, parent + '-swap')
            step_back(self)
            break
