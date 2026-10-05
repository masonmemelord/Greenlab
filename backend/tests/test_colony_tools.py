import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from scripts.prepare_colony_dataset import prepare
from scripts.compare_colony_rois import compare


class ColonyToolsTests(unittest.TestCase):
    def test_identical_and_empty_overlap(self):
        for points in ([], [{'x':1,'y':1},{'x':5,'y':1},{'x':5,'y':5}]):
            computer = {'file':'a.tif','page':1,'width':8,'height':8,'um_per_px':1,
                        'polygons': [[[p['x'],p['y']] for p in points]], 'elapsed_seconds':0.2}
            humans = [{'annotations':[dict(computer, reviewer=str(i), points=points, elapsed_seconds=5)]} for i in range(3)]
            rows = compare(computer, humans)
            self.assertTrue(all(row['iou'] == 1 and row['dice'] == 1 for row in rows))

    def test_dataset_geometry_and_split_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            roi = {'file':'a.tif','page':1,'width':8,'height':8,'note':'traced',
                   'points':[{'x':0,'y':0},{'x':8,'y':0},{'x':8,'y':8}]}
            (root/'rois.json').write_text(json.dumps({'annotations':[roi]}))
            entries = []
            for split in ('train','val'):
                image = root/f'{split}.tif'; Image.new('RGB',(8,8)).save(image)
                entries.append({'image':str(image),'rois':str(root/'rois.json'),'file':'a.tif','split':split})
            manifest = root/'manifest.json'; manifest.write_text(json.dumps(entries))
            prepare(manifest, root/'dataset')
            self.assertEqual((root/'dataset/labels/train/00000.txt').read_text(), '0 0.00000000 0.00000000 1.00000000 0.00000000 1.00000000 1.00000000\n')
            entries[1]['image'] = entries[0]['image']; manifest.write_text(json.dumps(entries))
            with self.assertRaises(ValueError): prepare(manifest, root/'leaked')
