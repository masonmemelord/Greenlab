# Segementation Logs
## Sep 18
## Next Goals 
I have to study some segmentation and see how I can feed my detection into it or whether I leave it as a standalone. Depending on how that research goes is how I will base my decisions moving forward. I will research the best segmentation models and stack them on top/integrate them into my Roboflow. All documentation moving forward will be done in the formats shown from Sep 21.
**Models I've been looking @**:
- SegmentAnythingModel(SAM3, `Meta`)
- MedSAM(SAM wrapper)
- YOLO 26


## Sep 21 — Transition from Object Detection to Instance Segmentation

### Objective
Determine whether a YOLO-based instance segmentation architecture can
improve cell localization and morphological measurement compared with
the existing YOLOv8 object-detection pipeline.

### Background / Rationale
The current YOLOv8 pipeline identifies cells using bounding boxes.
While this is sufficient for localization, bounding boxes do not
represent the actual boundaries of irregularly shaped cells.

Earlier development also identified discrepancies between automated
CV measurements and the manual CellSizer workflow. Segmentation may
provide a better representation for morphological measurements.

### Research Question
Does instance segmentation provide more reliable cell morphology
measurements than the existing bounding-box detection pipeline?

### Hypothesis
Pixel-level segmentation masks will provide more accurate estimates
of cell area and equivalent diameter than measurements derived from
bounding boxes.

### Method

**Baseline:** Current YOLOv8 detection pipeline

**Experimental Model:** YOLO segmentation architecture

**Dataset:** Existing Roboflow dataset

**Initial Metrics:**
- IoU
- Dice coefficient
- Precision
- Recall
- Area measurement error
- Equivalent diameter error

### Experimental Plan

**Phase 1:** Train segmentation model and compare against current
detection pipeline.

**Phase 2:** Deploy segmentation as an experimental feature for
side-by-side comparison.

**Phase 3:** Replace the existing detection architecture if
segmentation demonstrates sufficient reliability.

### Next Steps
- Establish baseline metrics for current YOLOv8 model
- Train first segmentation model
- Define test dataset
- Compare segmentation measurements against manual measurements

## Nov 23 - Updating scripts and images for Segmentation
Very short change for today. I'm doing small things over this thanksgiving break to set up my work for the winter. Luckily for me, when I detected these images I did it with masks and bounding boxes so all the hand-detection was done on the backend. On the programming side I just copied the detection script into the segmentation folder and changed to read for segmentation (model, parent, and detection type). I'm going to run the training set tonight.

**Training Run Results (50 Epochs)**
- Model: YOLO26n-seg
- Imgsz: 512
- Best Epoch: 14

### Next Steps
1. Build Masks and normalize images
2. Pulling metrics for masks
3. Instance matching (finding precision and recall)
4. Compare Detection versus Segmentation