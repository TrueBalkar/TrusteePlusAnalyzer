from ..tools.make_screenshots import make_screenshots
from ..navigation.navigator import step_back


def process_new_page(self, parent, screenshot=True):
    if screenshot is True:
        # logging.info(f'Making screenshots on page: {parent}...~cyan')
        make_screenshots(self, parent)
    step_back(self)
