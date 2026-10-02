import warnings
warnings.filterwarnings('ignore')

from ultralytics import YOLO

model = YOLO('yolov8s.pt')
model.train(
    data='Greenlab-Dataset-4/data.yaml',
    epochs=50,
    imgsz=640,
    patience=10,
    batch=4,
    workers=0
)