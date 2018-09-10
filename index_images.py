#coding:utf-8

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
from more_itertools import chunked
from time import time
import json
import os
import random
import requests
import sys
from util import iter_docs



if __name__ == "__main__":
    features_src = os.getenv('FEATURE_DIR', './features')

    ap = ArgumentParser(description="See script")
    ap.add_argument("--features_src", default=features_src,
                    help="Directory containing image feature docs.")
    ap.add_argument("--es_hosts", default="http://127.0.0.1:9200",
                    help="Comma-separated elasticsearch host URLs.")
    ap.add_argument("-b", "--batch_size", type=int, default=10,
                    help="Batch size for elasticsearch indexing.")
    args = vars(ap.parse_args())

    # Parse multiple hosts.
    es_hosts = args["es_hosts"].split(",")
    es_hosts_cycle = cycle(es_hosts)

    # Prepare the document structure.
    body = {
        "_index": "images",
        "_type": "image",
        "_aknn_uri": "aknn_models/aknn_model/images",
        "_aknn_docs": [
            # Populated below with structure:
            # {
            #     "_id": "...",
            #     "_source": {
            #         "any_fields_you_want": "...",
            #         "_aknn_vector": [0.1, 0.2, ...]
            #     }
            # }, ...
        ]
    }

    mapping = {
        "properties": {
            "_aknn_vector": {
                "type": "half_float",
                "index": False
            }
        }
    }

    # Check if the index exists and get its count.
    count_url = "%s/%s/%s/_count" % (next(es_hosts_cycle), body["_index"], body["_type"])
    req = requests.get(count_url)
    count = 0 if req.status_code == 404 else req.json()["count"]
    print("Found %d existing documents in index" % count)

    # If the index does not exist, create its mapping.
    if req.status_code == 404:
        print("Creating index %s" % body["_index"])
        index_url = "%s/%s" % (next(es_hosts_cycle), body["_index"])
        req = requests.put(index_url)
        assert req.status_code == 200, json.dumps(req.json())

        print("Creating mapping for type %s" % body["_type"])
        mapping_url = "%s/%s/%s/_mapping" % (
            next(es_hosts_cycle), body["_index"], body["_type"])
        requests.put(mapping_url, json=mapping)
        assert req.status_code == 200, json.dumps(req.json())

    # Create an iterable over the feature documents.
    docs = iter_docs(args["features_src"])

    # Bookkeeping for round-robin indexing.
    docs_batch = []
    tpool = ThreadPoolExecutor(max_workers=len(es_hosts))
    nb_round_robin_rem = len(es_hosts) * args["batch_size"]
    nb_indexed = 0
    T0 = -1

    for doc in docs:

        if T0 < 0:
            T0 = time()

        aknn_doc = {
            "_id": doc["id"],
            "_source": {
                "path": doc["path"],
                "_aknn_vector": doc["feature_vector"]
            }
        }

        docs_batch.append(aknn_doc)
        nb_round_robin_rem -= 1
        if nb_round_robin_rem > 0:
            continue

        futures = []
        for h, d in zip(es_hosts, chunked(docs_batch, args["batch_size"])):
            body["_aknn_docs"] = d
            post_url = f"{h}/_aknn_index"
            futures.append(tpool.submit(requests.post, post_url, json=body))
            print("Posting %d docs to host %s" % (len(body["_aknn_docs"]), h))

        for f, h in zip(as_completed(futures), es_hosts):
            res = f.result()
            if res.status_code != 200:
                print("Error at host: %s" % h, res.json(), file=sys.stderr)
                sys.exit(1)
            print("Response %d from host %s:" % (res.status_code, h), res.json())
            nb_indexed += res.json()["size"]

        print("Indexed %d docs in %d seconds = %.2lf docs / second" % (
            nb_indexed, time() - T0, nb_indexed / (time() - T0)))

        # Reset bookkeeping.
        nb_round_robin_rem = len(es_hosts) * args["batch_size"]
        docs_batch = []
