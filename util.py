#coding:utf-8

from PIL import Image
import numpy
import imagehash
from skimage import io, img_as_float
from skimage.exposure import histogram

def bool_to_float(v):
    if v is True:
        return 1.0
    else:
        return 0.0

def get_feature(img:Image) -> numpy.ndarray:
    h = imagehash.phash(img)
    return numpy.vectorize(bool_to_float)(h.hash.flatten())

def toColorNumber(r, g, b) -> numpy.ndarray:
    return (4 ** 0) * r.astype(numpy.float32) + (4 ** 1) * g.astype(numpy.float32) + (4 ** 2) * b.astype(numpy.float32)

def decreaseColor(d: numpy.ndarray) -> numpy.ndarray:
    d[(d >= 0) & (d < 64)] = 0 #32
    d[(d >= 64) & (d < 128)] = 1 #96
    d[(d >= 128) & (d < 192)] = 2 #160
    d[(d >= 192) & (d <= 255)] = 3 #224
    return d

def split(d: numpy.ndarray) -> tuple:
    return (d[:,:,0], d[:,:,1], d[:,:,2])

def merge(r, g, b) -> numpy.ndarray:
    result = numpy.empty(shape=(r.shape[0], r.shape[1], 3), dtype=numpy.uint8)
    result[:,:,0] = r
    result[:,:,1] = g
    result[:,:,2] = b
    return result

def get_feature_hist(inumpyut_image: Image) -> numpy.ndarray:
    """not using pillow"""
    image = numpy.asarray(inumpyut_image)
    image.flags.writeable = True
    r, g, b = split(image)

    r = decreaseColor(r)
    b = decreaseColor(b)
    g = decreaseColor(g)

    h = toColorNumber(r, g, b)
    return histogram(h, nbins=64)[0].astype(numpy.float32) / (image.shape[0] * image.shape[1])
