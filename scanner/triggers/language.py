from ..navigation.navigator import navigate
from ..tools.essentials import move_mouse
from ..tools.make_screenshots import make_screenshots
import pyautogui
import time


def handle_language(self, page_name, data):
    if page_name in self.language_page:
        navigate(self, path=page_name)
        process_language(self, data, page_name)
        return True
    return False


def process_language(self, data, page_name):
    buttons = data.where(data['type'] == 'object').dropna()
    languages = {
        'russian': buttons.iloc[1],
        'ukrainian': buttons.iloc[2],
        'english': buttons.iloc[0]
    }
    for language in languages.keys():
        move_mouse(self, languages[language]['x1'], languages[language]['y1'],
                   languages[language]['x2'], languages[language]['y2'], click=True)

        for main_screen in self.main_buttons.keys():
            navigate(self, main_screen)
            make_screenshots(self, f'{page_name}-{language}-{main_screen}')
            pyautogui.scroll(1)
            time.sleep(self.scroll_time * 2)
            self.blacklisted_pages.append(f'{page_name}-{language}-{main_screen}')
        navigate(self, path=page_name)
