import numpy as np
import openslide
import traceback


class OpenslideParser:
    def __init__(self, slide_path):
        self.slide_path = slide_path
        self.slide = openslide.OpenSlide(slide_path)

    def slide_properties(self):
        props = {}
        for _key in self.slide.properties.keys():
            props[_key] = self.slide.properties[_key]
        return props

    def region_pixel_data(self, left, top, width, height, level=0):
        resp = {}
        try:
            image = self.slide.read_region((left, top), level, (width, height))
            pixels = np.array(image.getdata())
            _image_width = int(int(width) / max([1, int(level) * 2]))
            _image_height = int(int(height) / max([1, int(level) * 2]))
            pixels = np.resize(pixels, (_image_width, _image_height, 4))
            resp['pixels'] = pixels.tolist()
            resp['success'] = True
            return resp
        except:
            resp['success'] = False
            resp['error'] = traceback.format_exc()
            return resp