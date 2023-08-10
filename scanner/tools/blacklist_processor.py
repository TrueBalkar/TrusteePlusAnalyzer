from difflib import SequenceMatcher
import logging


def check_if_blacklisted(self, text, blacklist=None):
    if blacklist is None:
        blacklist = self.blacklist
    if isinstance(text, str):
        for blacklist_item in blacklist:
            length = len(blacklist_item)
            ratio = (length - 1) / int(length * 1.1)
            if SequenceMatcher(a=blacklist_item, b=text).ratio() >= ratio:
                return True

    if isinstance(text, list):
        for item in text:
            for blacklist_item in blacklist:
                length = len(blacklist_item)
                ratio = (length - 1) / int(length * 1.1)
                if SequenceMatcher(a=blacklist_item, b=item['text']).ratio() >= ratio:
                    return True
    return False


def check_for_blacklisted_page(self, data):
    parent = data['parent'].iloc[0]
    if parent in self.blacklisted_pages:
        logging.info(f'Due to page {parent} being in blacklist, it will be skipped!~yellow')
        return True
    return False


def check_for_blacklisted_element(self, element):
    element_name = element['parent'] + '-' + str(element['image_id']) + ':' + str(element['element_id'])
    if check_if_blacklisted(self, element['text'], self.blacklist):
        logging.info(f'Due to element {element_name} being in blacklist, it will be skipped!~yellow')
        return True
    return False
