"""Convert explicit image/split/ROI assignments to a YOLO segmentation dataset.

Manifest: [{"image": "/path/image.tif", "rois": "/path/colony_rois.json",
            "file": "image.tif", "page": 1, "split": "train"}, ...]
Assign all planes/related fields from one biological specimen to the same split.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.imaging import read_plane


def prepare(manifest_path, output):
    manifest = json.loads(Path(manifest_path).read_text())
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output folder to avoid stale labels.')
    seen = {}
    prepared = []
    for entry in manifest:
        split = entry['split']
        if split not in {'train', 'val', 'test'}:
            raise ValueError('Split must be train, val, or test.')
        source = Path(entry['image']).resolve()
        if source in seen and seen[source] != split:
            raise ValueError('Planes from one source image cannot cross splits.')
        seen[source] = split
        annotations = json.loads(Path(entry['rois']).read_text())['annotations']
        matches = [a for a in annotations if a['file'] == entry['file'] and a['page'] == entry.get('page', 1)]
        if len(matches) != 1:
            raise ValueError('Each manifest entry needs exactly one saved annotation.')
        roi = matches[0]
        image, _ = read_plane(source.read_bytes(), roi['page'] - 1)
        width, height = image.size
        if (width, height) != (roi['width'], roi['height']):
            raise ValueError('ROI and image dimensions differ.')
        label = ''
        if roi['note'] == 'traced':
            points = roi['points']
            if len(points) < 3:
                raise ValueError('A colony polygon needs at least three points.')
            if any(not (0 <= p['x'] <= width and 0 <= p['y'] <= height) for p in points):
                raise ValueError('ROI extends outside image.')
            label = '0 ' + ' '.join(f"{p['x']/width:.8f} {p['y']/height:.8f}" for p in points) + '\n'
        elif roi['note'] != 'no colony':
            raise ValueError('Unknown annotation status.')
        prepared.append((split, image, label))
    if not {'train', 'val'}.issubset({item[0] for item in prepared}):
        raise ValueError('Include separate training and validation images.')
    for index, (split, image, label) in enumerate(prepared):
        image_dir = output / 'images' / split
        label_dir = output / 'labels' / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        image.save(image_dir / f'{index:05d}.png')
        (label_dir / f'{index:05d}.txt').write_text(label)
    config = f'path: {json.dumps(str(output))}\ntrain: images/train\nval: images/val\nnames:\n  0: colony\n'
    if any(item[0] == 'test' for item in prepared):
        config += 'test: images/test\n'
    (output / 'data.yaml').write_text(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('output')
    args = parser.parse_args()
    prepare(args.manifest, args.output)
