import numpy as np
import cv2


def create_mask(image):
    mask = np.zeros(image.shape)
    image = (image // 16) * 16
    for row, color in enumerate(image):
        if np.array_equal(color[0], color[-1]):
            mask[row, np.where(np.all(image[row] == color[0], axis=-1))] = 255
        else:
            first_color_row = np.where(np.all(image[row] == color[0], axis=-1))
            last_color_row = np.where(np.all(image[row] == color[-1], axis=-1))
            if len(first_color_row[0]) + (image.shape[1] * 0.2) > len(last_color_row[0]):
                mask[row, last_color_row[0]] = 255
            else:
                mask[row, first_color_row[0]] = 255
    mask = mask.astype('uint8')
    mask = abs(mask - 255).astype('uint8')
    cv2.floodFill(mask, None, (0, 0), [255, 255, 255])
    return mask


def redraw_mask(image, mask):
    image = (image // 16) * 16
    color = image[0, image.shape[1] // 2, :]
    for row, new_color in enumerate(image):
        if not np.array_equal(color, image[row, image.shape[1] // 2, :]):
            if not np.array_equal(color, image[row, 0, :]):
                if not np.array_equal(color, image[row, -1, :]):
                    mask[row] = [0, 0, 0]
    mask = mask.astype('uint8')
    return mask
