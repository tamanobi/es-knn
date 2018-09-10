#coding:utf-8

from pathlib import Path
from PIL import Image
from argparse import ArgumentParser
from itertools import cycle
import requests
from util import get_feature

ESHOSTS=cycle(['http://127.0.0.1:9200'])

def images(es_index, es_type, es_id):
    req = requests.get(f'{next(ESHOSTS)}/{es_index}/{es_type}/search0000/_aknn_search?k1=500&k2=10')
    hits = req.json()["hits"]["hits"]
    took_ms = req.json()["took"]
    query_img, neighbor_imgs = hits[0], hits[1:]

    res = requests.get(f'{next(ESHOSTS)}/{es_index}/{es_type}/search0000')
    print(res.text)

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

if __name__ == '__main__':
    args = get_args()

    input_image_path = Path(args['input_image_path'])
    img = Image.open(str(input_image_path))
    print(input_image_path)
    feature = get_feature(img)

    search_id = 'search0000'
    aknn_doc = {
        "_id": search_id,
        "_source": {
            "path": '',
            "_aknn_vector": feature.tolist()
        }
    }

    index_name = 'images'
    doc_type = 'image'
    body = {
        "_index": index_name,
        "_type": doc_type,
        "_aknn_uri": f"aknn_models/aknn_model/{index_name}",
        "_aknn_docs": [aknn_doc]
    }

    host = args['es_hosts']
    post_url = f"{host}/_aknn_index"
    res = requests.post(post_url, json=body)
    print(res.text)
    images('images', 'image', 'random')
    res = requests.delete(f'{host}/{index_name}/{doc_type}/{search_id}')
    print(res.text)


