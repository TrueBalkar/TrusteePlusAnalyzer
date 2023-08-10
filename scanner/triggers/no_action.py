from ..tools.image_similarity import check_similarity


def check_for_no_action(self, base_image, current_image):
    if check_similarity(self, base_image, current_image):
        return True
    return False
