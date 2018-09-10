#coding:utf-8

import numpy
from pathlib import Path
from PIL import Image
from argparse import ArgumentParser
import imagehash
from itertools import cycle
import requests

ESHOSTS=cycle(['http://127.0.0.1:9200'])

def images(es_index, es_type, es_id):
    # Parse elasticsearch ID. If "demo", pick a random demo image ID.
    if es_id.lower() == "demo":
        es_id = random.choice(DEMO_IDS)

    elif es_id.lower() == "random":
        body = {
            "_source": ["path"],
            "size": 1,
            "query": {
                "function_score": {
                    "query": {"match_all": {}},
                    "boost": 5,
                    "random_score": {},
                    "boost_mode": "multiply"
                }
            }
        }
        req_url = "%s/%s/%s/_search" % (next(ESHOSTS), es_index, es_type)
        req = requests.put("%s/%s" % (next(ESHOSTS), 'images'))
        req = requests.get(req_url, json=body)
        es_id = req.json()["hits"]["hits"][0]["_id"]

    # Get number of docs in corpus.
    req_url = "%s/%s/%s/_count" % (next(ESHOSTS), es_index, es_type)
    req = requests.get(req_url)
    count = req.json()["count"]

    # Get the nearest neighbors for the query image, which includes the image.
    req_url = "%s/%s/%s/%s/_aknn_search?k1=300&k2=5" % (
        next(ESHOSTS), es_index, es_type, '1')
    req = requests.get(req_url)
    hits = req.json()["hits"]["hits"]
    took_ms = req.json()["took"]
    query_img, neighbor_imgs = hits[0], hits[1:]

    print(took_ms, query_img, neighbor_imgs)

def get_args():
    ap = ArgumentParser(description='See script')
    ap.add_argument("input_image_path",
                    help="Input Image Path")
    ap.add_argument("--es_hosts", default="http://127.0.0.1:9200",
                    help="Comma-separated elasticsearch host URLs.")
    ap.add_argument("-k1", type=int, default=100,
                    help="k1")
    ap.add_argument("-k2", type=int, default=10,
                    help="k2")
    return vars(ap.parse_args())

def bool_to_float(v):
    if v is True:
        return 1.0
    else:
        return 0.0

def get_feature(img:Image) -> numpy.ndarray:
    h = imagehash.phash(img)
    return numpy.vectorize(bool_to_float)(h.hash.flatten())

if __name__ == '__main__':
    # args = get_args()
    # input_image_path = Path(args['input_image_path'])
    # img = Image.open(str(input_image_path))
    # feature = get_feature(img)
    images('images', 'image', 'random')


