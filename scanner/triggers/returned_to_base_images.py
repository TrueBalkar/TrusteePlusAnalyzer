from ..tools.image_similarity import check_similarity


def check_if_returned_to_base_images(self):
    # logging.info('Checking if returned to previous page...~yellow')
    # logging.info(f'Available pages to return to: {", ".join(self.base_images.keys())}...~yellow')
    self.screenshotMaker.make_screenshot()
    current_image = self.screenshotMaker.image
    for path, image in zip(reversed(self.base_images.keys()), reversed(self.base_images.values())):
        if check_similarity(self, image, current_image):
            path = path.split('-')
            if path[-1].isdigit():
                path.pop(-1)
            self.current_position = path
            return True
    return False
