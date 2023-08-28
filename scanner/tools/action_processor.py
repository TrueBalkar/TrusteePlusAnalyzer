import logging
from ..triggers.no_action import check_for_no_action
from ..triggers.opened_browser import check_for_opened_browser, process_opened_browser
from ..triggers.changed_page import check_for_changed_page, process_changed_page
from ..triggers.text_input import check_for_text_input, process_text_input
from ..triggers.dropdown import check_for_dropdown_menu, process_dropdown_menu
from ..triggers.returned_to_base_images import check_if_returned_to_base_images
from ..triggers.new_page import process_new_page
from ..navigation.navigator import navigate


def check_action_kind(self, base_image):
    self.screenshotMaker.make_screenshot()
    current_image = self.screenshotMaker.image

    if check_for_no_action(self, base_image, current_image):
        return 'No action'

    if check_for_opened_browser(self, current_image):
        return 'Open browser'

    if check_for_changed_page(self, base_image, current_image):
        return 'Changed current page'

    if check_for_text_input(current_image):
        return 'Text input'

    if check_for_dropdown_menu(current_image):
        return 'Dropdown menu'

    if check_if_returned_to_base_images(self):
        return 'Returned to previous page'
    return 'New page'


def process_action(self, status, x1, y1, x2, y2, elements_on_page, parent, send_info=True):
    match status:
        case 'Text input':
            process_text_input(self, x1, y1, x2, y2)
        case 'Open browser':
            process_opened_browser(self, parent)
        case 'No action':
            pass
        case 'Changed current page':
            process_changed_page(self, y1=y1, y2=y2, elements_on_page=elements_on_page)
        case 'Dropdown menu':
            process_dropdown_menu(self, parent=parent, screenshot=send_info)
        case 'Returned to previous image':
            navigate(self, path=parent)
        case 'New page':
            process_new_page(self, parent=parent, screenshot=send_info)
