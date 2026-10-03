import warnings
warnings.filterwarnings('ignore')

from pathlib import Path
from ultralytics import YOLO

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BASE_MODEL = BACKEND_ROOT / "ml" / "weights" / "base" / "yolov8s.pt"
DATA_CONFIG = BACKEND_ROOT / "ml" / "datasets" / "object_detection" / "greenlab_v4" / "data.yaml"
RUNS_DIR = BACKEND_ROOT / "ml" / "runs" / "detection"

model = YOLO(str(BASE_MODEL))
model.train(
    data=str(DATA_CONFIG),
    project=str(RUNS_DIR),
    epochs=50,
    imgsz=640,
    patience=10,
    batch=4,
    workers=0
)
