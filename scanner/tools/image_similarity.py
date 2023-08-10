from sewar.full_ref import sam
import numpy as np


def check_similarity(self, image_1, image_2, confidence_coefficient=None):
    if not confidence_coefficient:
        confidence_coefficient = self.similarity_confidence_coefficient
    similarity = sam(image_1, image_2)

    # logging.info(f'Two images similarity: {similarity}~gray')
    if similarity <= confidence_coefficient or similarity is np.NaN:
        return True
    return False
