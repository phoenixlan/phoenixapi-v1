from pyramid.interfaces import IRendererFactory, IRenderer

import io

import logging
log = logging.getLogger(__name__)

class PillowRendererFactory():
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        system["request"].response.headers["Content-Type"] = "image/png"
        system["request"].response.headers["Content-Disposition"] = "attachment; filename=\"file.png\""
        img_byte_arr = io.BytesIO()
        value.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()