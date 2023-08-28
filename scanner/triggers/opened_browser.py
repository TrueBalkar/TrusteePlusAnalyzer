from ..object_searcher.create_mask import create_mask
from ..navigation.navigator import step_back


def check_for_opened_browser(self, image):
    image_slice = image[int(self.height * 0.005):int(self.height * 0.045),
                        int(self.width * 0.91):int(self.width * 0.99)]
    mask_image = create_mask(image_slice, reduce_quality=False)

    lines = []
    for row in range(mask_image.shape[0] - 1):
        if abs((mask_image[row].mean() / 255) - (mask_image[row + 1].mean() / 255)) > 0.1:
            lines.append(row)
    if len(lines) < 2:
        return False
    lines = [lines[0], lines[-1]]
    for column in range(mask_image.shape[1] - 1):
        if abs((mask_image[lines[0]:lines[1], column].mean() / 255) - (
                mask_image[lines[0]:lines[1], column + 1].mean() / 255)) > 0.2:
            lines.append(column)

    if len(lines) < 4:
        return False

    lines = [lines[0], lines[1], lines[2], lines[-1]]

    image_slice = image_slice[lines[0] + 1:lines[1], lines[2] + 1:lines[3]]
    for row_num, row in enumerate(image_slice):
        for color_num, color in enumerate(row):
            if color[0] == color[1] == color[2]:
                image_slice[row_num][color_num] = [0, 0, 0]
            elif color[0] > color[1] and color[0] > color[2]:
                image_slice[row_num][color_num] = [255, 0, 0]
            elif color[1] > color[0] and color[1] > color[2]:
                image_slice[row_num][color_num] = [0, 255, 0]
            elif color[2] > color[0] and color[2] > color[1]:
                image_slice[row_num][color_num] = [0, 0, 255]
    scores = [image_slice[:, :, channel].sum() / image_slice.sum() > 0.35 for channel in range(3)]
    if any(scores):
        return True
    return False


def process_opened_browser(self, page_name):
    self.screenshotMaker.make_screenshot()
    self.images.append((self.screenshotMaker.image, page_name, 1))
    self.blacklisted_pages.append(page_name)
    step_back(self)
