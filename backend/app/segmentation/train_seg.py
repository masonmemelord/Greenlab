#from train.py
import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
from ultralytics import YOLO

BACKEND_ROOT = Path(__file__).resolve().parents[2]
BASE_MODEL = BACKEND_ROOT / "ml" / "weights" / "base" / "yolo26n-seg.pt"
DATA_CONFIG = BACKEND_ROOT / "ml" / "datasets" / "object_detection" / "greenlab_v4" / "data.yaml"
RUNS_DIR = BACKEND_ROOT / "ml" / "runs" / "segmentation"

model = YOLO(str(BASE_MODEL))
model.train(
    data=str(DATA_CONFIG),
    project=str(RUNS_DIR),
    epochs=50,
    imgsz=512,
    patience=10,
    batch=4,
    workers=0
)

