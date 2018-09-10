#coding:utf-8

from argparse import ArgumentParser
from pathlib import Path
from tqdm import tqdm
import os
from PIL import Image
import json
from util import get_feature

def get_image_path(image_dir:Path) -> list:
    image_paths = []
    for p in tqdm(image_dir.glob('**/*'), desc='image_paths'):
        if p.suffix in ['.jpg', '.png', '.jpeg']:
            image_paths.append(p)
    return image_paths

if __name__ == '__main__':
    image_dir = os.getenv('IMAGE_DIR', './images')

    ap = ArgumentParser(description='See script')
    ap.add_argument('-d', '--image_dir', type=str, default=image_dir,
                    help='image directory')
    ap.add_argument('-o', '--output_dir', type=str, default='features',
                    help='Directory output json')

    args = vars(ap.parse_args())
    image_dir = Path(args['image_dir'])
    assert image_dir.exists(), 'no image directory found.'
    output_dir = Path(args['output_dir'])
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = get_image_path(image_dir)
    features = []
    for i, image_path in enumerate(tqdm(image_paths, desc='extracting')):
        binary_array = get_feature(Image.open(str(image_path)))
        features.append({'id':str(i), 'path':str(image_path), 'feature_vector':binary_array.tolist()})

    for i, feature in enumerate(tqdm(features, desc='writing')):
        fname = f'features-{i:08}.json'
        with open(str(output_dir / fname), 'w') as f:
            json.dump(feature, f)
