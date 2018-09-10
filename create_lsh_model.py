#coding: utf-8

from argparse import ArgumentParser
from sys import stderr
from time import time
import json
import os
import random
import requests
import gzip

def iter_docs(src):
    iter_ = os.scandir(src)

    for i, fobj in enumerate(iter_):
        with gzip.open(fobj.path) as fp:
            yield json.loads(fp.read().decode())


if __name__ == "__main__":
    ap = ArgumentParser(description="See script")
    ap.add_argument("--es_host", default="http://127.0.0.1:9200",
                    help="URL of single elasticsearch server.")
    ap.add_argument("--aknn_tables", type=int, default=48)
    ap.add_argument("--aknn_bits", type=int, default=4)
    ap.add_argument("--aknn_dimensions", type=int, default=64)
    ap.add_argument("-p", type=float, default=0.2,
                    help="Prob. of accepting a feature document as a sample.")
    args = vars(ap.parse_args())

    # Prepare the Aknn model mapping.
    mapping = {
        "properties": {
            "_aknn_midpoints": {
                "type": "half_float",
                "index": False
            },
            "_aknn_normals": {
                "type": "half_float",
                "index": False
            },
            "_aknn_nb_bits_per_table": {
                "type": "short",
                "index": False
            },
            "_aknn_nb_dimensions": {
                "type": "short",
                "index": False
            },
            "_aknn_nb_tables": {
                "type": "short",
                "index": False
            }
        }
    }

    # Body for posting new vectors.
    body = {
        "_index": "aknn_models",
        "_type": "aknn_model",
        "_id": "images",
        "_source": {
            "_aknn_description": "AKNN model for images on the twitter public stream",
            "_aknn_nb_dimensions": args["aknn_dimensions"],
            "_aknn_nb_tables": args["aknn_tables"],
            "_aknn_nb_bits_per_table": args["aknn_bits"]
        },
        "_aknn_vector_sample": [
            # Populated below.
        ]
    }

    # Delete and remake the index.
    print("Deleting index %s" % body["_index"])
    index_url = "%s/%s" % (args["es_host"], body["_index"])
    req = requests.delete(index_url)
    assert req.status_code == 200, "Failed to delete index: %s" % json.dumps(req.json())

    print("Creating index %s" % body["_index"])
    req = requests.put(index_url)
    assert req.status_code == 200, "Failed to create index: %s" % json.dumps(req.json())

    # Put the mapping. This can fail if you already have this index/type setup.
    print("Creating mapping for index %s" % body["_index"])
    mapping_url = "%s/%s/%s/_mapping" % (args["es_host"], body["_index"], body["_type"])
    req = requests.put(mapping_url, json=mapping)
    assert req.status_code == 200, "Failed to create mapping: %s" % json.dumps(req.json())

    # Create an iterable over the feature documents.
    docs = iter_docs('./features')

    # Populate the vector sample by randomly sampling vectors from iterable.
    nb_samples = 2 * args["aknn_bits"] * args["aknn_tables"]
    #print("Sampling %d feature vectors from %s" % (nb_samples, args["features_source"]))
    while len(body["_aknn_vector_sample"]) < nb_samples:
        vec = next(docs)["feature_vector"]
        #vec = {"id":"1", "img_pointer":4, "imagenet_labels":"dog", "feature_vector":[0,0,1,1]}
        body["_aknn_vector_sample"].append(vec)

    print("Posting to Elasticsearch")
    t0 = time()
    print("%s/_aknn_create" % args["es_host"])
    res = requests.post("%s/_aknn_create" % args["es_host"], json=body)
    if res.status_code == requests.codes.ok:
        print("Successfully built model in %d seconds" % (time() - t0))
    else:
        print("Failed with error code %d" % res.status_code, file=stderr)
        print(res.text)
