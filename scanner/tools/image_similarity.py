from sewar.full_ref import sam
import numpy as np

# image_1 = templates/511.09.08 (10d)/wallet/2_original.png
# image_2 = templates/511.09.08 (10d)/wallet/3_original.png
# full_image = pref: 0.03467996000108542, sim: 0.18401169962543684
# 2 times smaller image (vertically) = pref: 0.017364569997880608, sim: 0.18421651983670295
# 2 times smaller image (horizontally) = pref: 0.020462298998609185, sim: 0.1837093663633069
# 4 times smaller image = perf: 0.009299901001213584, sim: 0.18393590268823856
# 9 times smaller image = pref: 0.004332650001742877, sim: 0.18597549177291187
# 16 times smaller image = pref: 0.0025838239962467924, sim: 0.18178099371141784


def check_similarity(self, image_1, image_2, confidence_coefficient=None, reduce_quality=True):
    if not confidence_coefficient:
        confidence_coefficient = self.similarity_confidence_coefficient
    if reduce_quality:
        image_1 = np.array(image_1[::4, ::4])
        image_2 = np.array(image_2[::4, ::4])
    similarity = sam(image_1, image_2)
    # logging.info(f'Two images similarity: {similarity}~gray')
    if similarity <= confidence_coefficient or similarity is np.NaN:
        return True
    return False
