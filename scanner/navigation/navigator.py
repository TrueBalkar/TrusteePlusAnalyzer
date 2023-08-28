import logging
import time
import pyautogui
from .essentials import scroll, move_mouse, go_back
from ..triggers.returned_to_base_images import check_if_returned_to_base_images
from ..tools.image_similarity import check_similarity


def navigate(self, path):
    # if len(self.current_position) > 1:
    #     if not check_if_returned_to_base_images(self):
    #         step_back(self)
    logging.info(f'Current position: {"-".join(self.current_position)}~cyan')
    logging.info(f'Navigating to position: {path}~cyan')
    current_full_path = ''
    path = path.split('-')
    current_scrolls = 1
    # if self.current_position[-1].isdigit():
    #     self.current_position.pop(-1)
    backtrack(self, path)
    # logging.info(f'Backtracked to: {self.current_position}~yellow')
    position_adjusted = check_for_adjusted_position(self, path)
    if position_adjusted is not None:
        if position_adjusted is False:
            return navigate(self, '-'.join(path))
        else:
            current_scrolls = position_adjusted
    # logging.info(f'Adjusted position to: {self.current_position}~yellow')
    for index, path_element in enumerate(path):
        while len(self.current_position) <= index:
            self.current_position.append('')
        if path_element != self.current_position[index]:
            logging.info(f'Navigation step: {index + 1} of {len(path)}. '
                         f'Currently navigating to {current_full_path + "-" if current_full_path != "" else ""}'
                         f'{path_element} from {"-".join(self.current_position)[:-1]}~cyan')
        match check_for_action(self, index, path_element):
            case 'Same position':
                current_full_path = process_same_position(self, path_element, current_full_path)
            case 'Main page':
                current_full_path = process_main_page(self, path_element)
            case 'Different position':
                current_full_path, current_scrolls = process_different_position(self, path_element, current_full_path,
                                                                                current_scrolls)
                if current_full_path == 'Error':
                    return 'Error'
    return 'Done'


def backtrack(self, path):
    while len(self.current_position) > len(path):
        self.base_images.popitem()
        self.current_position.pop(-1)
        if step_back(self) == 'Crashed':
            return navigate(self, '-'.join(path))


def check_for_adjusted_position(self, path):
    adjust_position_status = adjust_position(self, path)
    if adjust_position_status == 'Error':
        return False
    elif isinstance(adjust_position_status, int):
        return adjust_position_status
    return None


def adjust_position(self, path):
    for index in range(len(self.current_position)):
        if self.current_position[index] != path[index]:
            logging.info(f'{self.current_position[index]} != {path[index]}, index: {index}~yellow')
            current_scrolls = int(self.current_position[index].split(':')[0]) if index != 0 else 1
            destination_scrolls = int(path[index].split(':')[0]) if index != 0 else 1
            index = index if index != 0 else 1
            while len(self.current_position) > index:
                old_position_depth = len(self.current_position)
                if step_back(self) == 'Crashed':
                    return 'Error'
                logging.info(f'Adjusted position to: {self.current_position}~yellow')
                if old_position_depth == len(self.current_position):
                    self.base_images.popitem()
                    self.current_position.pop(-1)
            if current_scrolls > destination_scrolls:
                move_mouse(self, self.width // 2, self.height // 2)
                pyautogui.scroll(1)
                time.sleep(self.loading_time)
                current_scrolls = 1
            return current_scrolls


def check_for_action(self, index, path_element):
    if path_element == self.current_position[index]:
        return 'Same position'
    elif path_element in self.main_buttons.keys():
        return 'Main page'
    else:
        return 'Different position'


def process_main_page(self, path_element):
    self.base_images = {}
    move_mouse(self, rel_x1=self.main_buttons[path_element][0], rel_y1=self.main_buttons[path_element][1],
               start_x=0, start_y=0, sleep_time=self.loading_time * 2, click=True, sleep=True)
    self.screenshotMaker.make_screenshot()
    self.base_images[path_element] = self.screenshotMaker.image
    self.current_position[0] = path_element
    return path_element


def process_same_position(self, path_element, current_full_path):
    if path_element in self.main_buttons.keys():
        current_full_path += path_element
        return current_full_path
    else:
        current_full_path += '-' + path_element
        return current_full_path


def process_different_position(self, path_element, current_full_path, current_scrolls):
    self.current_position[-1] = path_element
    image_id, element_id = [int(i) for i in path_element.split(':')]
    x1, y1, x2, y2 = self.app_details[['x1', 'y1', 'x2', 'y2']].where(
        (self.app_details['parent'] == current_full_path) &
        (self.app_details['image_id'] == image_id) &
        (self.app_details['element_id'] == element_id)
    ).dropna().values[0]
    logging.info(f'Amount of scrolling: current_scrolls: {current_scrolls}, image_id: {image_id}~cyan')
    scroll(self, image_id - current_scrolls)
    current_scrolls = 1
    if check_if_navigated(self, current_full_path, x1, y1, x2, y2) == 'Error':
        return 'Error', None
    if path_element not in self.main_buttons.keys():
        current_full_path += '-'
    current_full_path += path_element
    return current_full_path, current_scrolls


def check_if_navigated(self, current_full_path, x1, y1, x2, y2):
    self.screenshotMaker.make_screenshot()
    self.base_images[current_full_path] = self.screenshotMaker.image
    move_mouse(self, x1, y1, x2, y2, click=True, sleep=True)
    self.screenshotMaker.make_screenshot()
    old_image = self.screenshotMaker.image
    if check_similarity(self, old_image, self.base_images[current_full_path]):
        move_mouse(self, x1, y1, x2, y2, click=True, sleep=True)
        self.screenshotMaker.make_screenshot()
        old_image = self.screenshotMaker.image
        if check_similarity(self, old_image, self.base_images[current_full_path]):
            logging.info(f"Couldn't navigate properly... Aborting!~red")
            self.current_position.pop(-1)
            return 'Error'


def step_back(self):
    logging.info(f'Available steps to go back to... {self.base_images.keys()}~red')
    go_back()
    time.sleep(self.go_back_time)
    destination = '-'.join(self.current_position)
    counts = 0
    while not check_if_returned_to_base_images(self):
        if check_similarity(self, self.main_screen, self.screenshotMaker.image) or \
                (counts % 25 == 0 and counts != 0):
            start_app(self)
            if destination != self.main_app_screen_page:
                navigate(self, destination)
            logging.info(f'Returning to image_id: {self.scrolls}~red')
            scroll(self, self.scrolls - 1)
            self.screenshotMaker.make_screenshot()
            self.base_images[destination] = self.screenshotMaker.image
            return 'Crashed'
        elif counts % 15 == 0 and counts != 0:
            self.screenshotMaker.make_screenshot()
            current_image = self.screenshotMaker.image
            exit_app(self)
            self.screenshotMaker.make_screenshot()
            if check_similarity(self, current_image, self.screenshotMaker.image):
                process_app_not_responding(self)
        elif counts % 3 == 0 and counts != 0:
            logging.info(f'Trying to step back once again...~red')
            go_back()
            time.sleep(self.go_back_time)
        else:
            logging.info(f'Something went wrong, when tried going back... '
                         f'Waiting for {self.go_back_time} sec(s)~red')
            time.sleep(self.go_back_time)
        counts += 1
    else:
        if counts > 2 and len(self.current_position) == 1:
            pyautogui.scroll(1)
            time.sleep(self.scroll_time * 2)
    return 'OK'


def exit_app(self):
    logging.info(f'Restarting app!~red')
    for i in range(self.max_depth + 1):
        pyautogui.hotkey('ctrl', 'backspace')
        time.sleep(self.go_back_time)


def start_app(self):
    logging.info(f'Currently on main screen... Returning to {self.main_app_screen_page}...~red')
    move_mouse(self, rel_x1=self.app_coordinates['x'], rel_y1=self.app_coordinates['y'], click=True, sleep=True)
    self.base_images = {}
    time.sleep(self.loading_time * 5)
    move_mouse(self, self.width // 2, self.height // 2)
    pyautogui.scroll(1)
    time.sleep(self.scroll_time * 2)
    self.screenshotMaker.make_screenshot()
    self.base_images[self.main_app_screen_page] = self.screenshotMaker.image
    self.current_position = [self.main_app_screen_page]


def process_app_not_responding(self):
    logging.info(f'App not responding. Restarting app!~red')
    self.screenshotMaker.make_screenshot()
    current_image = self.screenshotMaker.image
    move_mouse(self, rel_x1=self.width // 2, rel_y1=int(self.height*0.48), click=True, sleep=True)
    self.screenshotMaker.make_screenshot()
    if check_similarity(self, current_image, self.screenshotMaker.image):
        move_mouse(self, rel_x1=self.width // 2, rel_y1=int(self.height*0.48), click=True, sleep=True)
        self.screenshotMaker.make_screenshot()
    pyautogui.hotkey('ctrl', 'h')
    time.sleep(self.loading_time * 5)
    self.current_position = [self.main_app_screen_page]
