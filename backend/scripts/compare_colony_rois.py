"""Compare one computer image against three independently saved human outlines.
Output agreement with each reviewer, not a claim of ground-truth accuracy.
"""
import argparse
import json
import math
from PIL import Image, ImageDraw
import numpy as np


def mask(polygons, width, height):
    canvas = Image.new('1', (width, height))
    draw = ImageDraw.Draw(canvas)
    for polygon in polygons:
        if len(polygon) >= 3:
            draw.polygon([tuple(p) for p in polygon], fill=1)
    return np.asarray(canvas, dtype=bool)


def compare(computer, humans):
    cmask = mask(computer['polygons'], computer['width'], computer['height'])
    rows = []
    for export in humans:
        matching = [a for a in export['annotations'] if a['file'] == computer['file'] and a['page'] == computer['page']]
        if len(matching) != 1:
            raise ValueError('Each reviewer needs one matching image/page.')
        roi = matching[0]
        if (roi['width'], roi['height']) != (computer['width'], computer['height']):
            raise ValueError('Image dimensions differ.')
        if not math.isclose(roi['um_per_px'], computer['um_per_px']):
            raise ValueError('Calibration differs.')
        hmask = mask([[(p['x'], p['y']) for p in roi['points']]], roi['width'], roi['height'])
        intersection = int((hmask & cmask).sum())
        union = int((hmask | cmask).sum())
        human_area, computer_area = int(hmask.sum()), int(cmask.sum())
        rows.append({'reviewer': roi['reviewer'],
                     'iou': intersection / union if union else 1.0,
                     'dice': 2 * intersection / (human_area + computer_area) if human_area + computer_area else 1.0,
                     'area_error_percent': 100 * abs(computer_area - human_area) / human_area if human_area else None,
                     'human_seconds': roi['elapsed_seconds'], 'computer_inference_seconds': computer['elapsed_seconds']})
    if len({r['reviewer'] for r in rows}) != 3:
        raise ValueError('Provide three distinct reviewer IDs.')
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('computer')
    parser.add_argument('humans', nargs=3)
    args = parser.parse_args()
    print(json.dumps(compare(json.load(open(args.computer)), [json.load(open(p)) for p in args.humans]), indent=2))
