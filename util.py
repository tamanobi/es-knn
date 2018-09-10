#coding:utf-8

from PIL import Image
import numpy
import imagehash

def bool_to_float(v):
    if v is True:
        return 1.0
    else:
        return 0.0

def get_feature(img:Image) -> numpy.ndarray:
    h = imagehash.phash(img)
    return numpy.vectorize(bool_to_float)(h.hash.flatten())

