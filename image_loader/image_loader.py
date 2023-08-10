from PIL import Image
import cv2
import numpy as np
import logging
import pyautogui


class ScreenshotMaker:
    def __init__(self):
        self.image = None
        self.screen_height = None
        self.screen_width = None
        self.region = [None, None, None, None]
        self.define_region_()

    def define_region_(self):
        image = np.array(pyautogui.screenshot())
        self.screen_height = image.shape[0]
        self.screen_width = image.shape[1]
        self.region = [0, 0, self.screen_width, self.screen_height]
        image = (image // 4) * 4
        background_color = image[-1, -1]
        for i in range(-1, -self.screen_width, -1):
            if not np.array_equal(image[self.screen_height // 2, i], background_color):
                self.region[2] = self.screen_width + i
                break
        self.region[1] = self.screen_height * 0.02

    def define_region(self):
        image = np.array(pyautogui.screenshot())
        self.screen_height = image.shape[0]
        self.screen_width = image.shape[1]
        self.region = [0, 0, self.screen_width, self.screen_height]
        image = (image // 16) * 16
        mask = []
        for row in image:
            mask.append(((row == image[0][image.shape[1] // 2]) == (row == image[image.shape[0] // 2][0])) * 255)
        mask = np.array(mask).astype('uint8')
        x_arr = []
        y_arr = []
        for row in range(self.screen_width - 1):
            if (mask[:, row] / 255).mean() > 0.2:
                x_arr.append(row)
        self.region[0] = x_arr[0]
        self.region[2] = x_arr[-1] - x_arr[0]

        for col in range(self.screen_height - 1):
            if (mask[col, :] / 255).mean() > 0.2:
                y_arr.append(col)
        self.region[1] = int(y_arr[0] + (y_arr[-1] - y_arr[0]) * 0.03)
        self.region[3] = y_arr[-1] - self.region[1]

    def make_screenshot(self, x=None, y=None, width=None, height=None):
        if x is None:
            x = self.region[0]
        if y is None:
            y = self.region[1]
        if width is None:
            width = self.region[2]
        if height is None:
            height = self.region[3]
        self.image = pyautogui.screenshot(region=(x, y, width, height))
        self.image = np.array(self.image)


class ImageClass:
    def __init__(self):
        self.image = None
        self.image_gray = None
        self.mask_objects = None
        self.mask_text_v1 = None
        self.mask_text_v2 = None
        self.result_image = None
        self.scale_image = None
        self.scale_objects = None
        self.scale_text = None
        self.filter_objects = ((230, 230, 230), (235, 235, 235))
        self.filter_text_v1 = ((0, 0, 0), (130, 130, 130))
        self.filter_text_v2 = ((200, 200, 200), (255, 255, 255))
        self.inverse_filter_object = False
        self.write_log = False

    def get_masks(self):
        if self.write_log:
            logging.info('[DRAWING MASKS FOR IMAGES]')
        self.image_gray = cv2.cvtColor(np.array(self.image), cv2.COLOR_RGB2GRAY)
        self.mask_objects = np.array(self.image)
        self.mask_objects = cv2.inRange(np.array(self.image), self.filter_objects[0], self.filter_objects[1])
        if self.inverse_filter_object:
            self.mask_objects = abs(255 - self.mask_objects)
        self.mask_text_v1 = cv2.inRange(np.array(self.image), self.filter_text_v1[0], self.filter_text_v1[1])
        self.mask_text_v2 = cv2.inRange(np.array(self.image), self.filter_text_v2[0], self.filter_text_v2[1])

    def resize_images(self):
        self.image = scale_image(self.image, self.scale_image)
        self.image_gray = get_opencv_image(scale_image(get_pil_image(self.image_gray), self.scale_image))
        self.mask_objects = get_opencv_image(scale_image(get_pil_image(self.mask_objects), self.scale_objects))
        self.mask_text_v1 = get_opencv_image(scale_image(get_pil_image(self.mask_text_v1), self.scale_text))
        self.mask_text_v2 = get_opencv_image(scale_image(get_pil_image(self.mask_text_v2), self.scale_text))

    def blur_masks(self, matrix_size):
        self.mask_text_v1 = cv2.medianBlur(self.mask_text_v1, matrix_size)
        self.mask_text_v2 = cv2.medianBlur(self.mask_text_v2, matrix_size)
        self.image_gray = cv2.medianBlur(self.image_grey, matrix_size)

    def create_clean_result_image(self):
        self.result_image = np.array(self.image)

    def show_image(self, image):
        Image.fromarray(image).show()

    def create_new_mask(self, new_filter, invert=False):
        new_mask = cv2.inRange(np.array(self.image), new_filter[0], new_filter[1])
        if invert:
            new_mask = abs(255 - new_mask)
        Image.fromarray(new_mask).show()


def get_pil_image(image):
    return Image.fromarray(image)


def get_opencv_image(image):
    return np.array(image)


def scale_image(image, scale):
    return image.resize((image.size[0] * scale, image.size[1] * scale))
