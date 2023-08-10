import os
from PIL import Image


def write_image(self, path, image_name, image):
    path = self.template_path + path.replace('-', '/') + '/'
    image_path = path + image_name + '.png'
    if not os.path.exists(path):
        os.makedirs(path)
    Image.fromarray(image).save(image_path)


def write_json(self, template):
    template.to_json(self.template_path + 'templates.json')
