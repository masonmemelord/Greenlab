import torch
import os
from ultralytics import YOLO
from ultralytics.engine.results import Results

class CellDetector:
    def __init__(self, model_path='models/best.pt'):
        if torch.backends.mps.is_available():
            self.device = 'mps'
        elif torch.cuda.is_available():
            self.device = 'cuda'
        else:
            self.device = 'cpu'

        print(f"Using device: {self.device}")

        try:
            self.model = YOLO(model_path)
            self.model.to(self.device)
            print(f"Loaded model from {model_path}")
        except Exception as e:
            raise RuntimeError(
                f"Could not load model from '{model_path}'. "
                f"Please make sure the weights file is in your models/ folder."
            )

    def predict(self, image, confidence=0.25, iou=0.4):
        """Runs detection on a PIL image using YOLOv8."""
        results = self.model.predict(
            source=image,
            conf=confidence,
            iou=iou,
            device=self.device,
            imgsz=1280,
            augment=True,
            agnostic_nms=True,
            max_det=1000,
        )
        return results[0]

    def get_metadata(self, results: Results, cell_types: dict = None):
        """Extracts cell metadata from results."""
        cells = []
        for i, box in enumerate(results.boxes):
            class_id = int(box.cls[0].item())
            cell_type = cell_types.get(class_id, f"Class {class_id}") if cell_types else results.names.get(class_id, f"Class {class_id}")
            cells.append({
                "Cell(s)": i + 1,
                "Cell Type": cell_type,
                "Confidence Score": round(float(box.conf[0].item()), 3),
                "Class ID": class_id,
                "Coordinates": box.xyxy[0].tolist(),
                "Center & Size": box.xywh[0].tolist(),
            })
        return cells