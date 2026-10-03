# Tulane Cell Detection
This is the repository for training the Tulane Cell Detection and Segmentation App using YOLO. The goal for the app/research is for me to get the best possible CV/Segmentation results throughout the span of development.

# How to get around
- Backend: where you will the what makes the code work. Datasets, Python files/scripts, etc.
- Frontend: The logic for the actual website. No need to look into this unless you like knowing how pages look and what tables return.
- Research: Where the bulk of my thoughts, processes and findings will go over. Includes my personal logs, experiment goals, and actual research papers I source.

# Features

## What is Computer Vision
Computer Vision is a subset of machine learning that focuses on identifying certain objects using datasets that train and detect objects (usually using bounding boxes) to analyze and identify objects in any given space.

## What is Segmentation 
Also a subset of ML. Think of it like a boosted version of Computer Vision. It takes all the elements of CV and thanks to masks (pixel-outlining) provides cleaner, more accurate (assuming trained correctly) outlines.

## How Manual Tracing Fits In
The classic way of detection. Albeit highly unlikely a pipe breaks in this workflow, manual tracing serves as a backup as well as source to train future datasets.

# Research Process and Important Terms

## Research Process
1. Create a clean labeled validation set from manual tracing. 
*Until the dataset has enough viable images to self-train*
2. Decide the metrics and acceptable error thresholds. *~75% accuracy or Higher*
3. Establish and compare against baseline *YOLO-v8 object detection*
4. Train/test multiple model types on identical splits.
5. Select the model based on accuracy, consistency, speed, and explainability

## Important Terms
Below are some important terms and their definitions and/or formulas

### IoU (Intersection over Union)

$$
\text{IoU} = \frac{|A \cap B|}{|A \cup B|}
$$

- **Purpose:** Measures how closely a predicted region or bounding box matches the ground-truth region.
- **Area of intersection** $(A \cap B)$: Pixels shared by the predicted and ground-truth regions.
- **Area of union** $(A \cup B)$: All pixels contained in either region.

$$
|A \cup B| = |A| + |B| - |A \cap B|
$$

- **Range:** $0$ to $1$, where $1$ means a perfect overlap.

### Dice Coefficient

$$
\text{DSC} = \frac{2|A \cap B|}{|A| + |B|}
$$

- **Purpose:** Measures overlap between predicted and ground-truth segmentation masks.
- **Range:** $0$ to $1$, where $1$ means a perfect match.
- Dice is often useful when the cell or colony occupies a small part of the image.

### Precision

$$
\text{Precision} = \frac{TP}{TP + FP}
$$

- **Purpose:** Measures how many predicted cells are actually cells.
- $TP$ (**true positives**): Correctly detected cells.
- $FP$ (**false positives**): Predicted cells that do not match a real labeled cell.
- **Interpretation:** High precision means the model produces few false detections.

### Recall

$$
\text{Recall} = \frac{TP}{TP + FN}
$$

- **Purpose:** Measures how many real cells the model successfully finds.
- $TP$ (**true positives**): Correctly detected cells.
- $FN$ (**false negatives**): Real labeled cells missed by the model.
- **Interpretation:** High recall means the model misses few cells.

### Area Measurement Error

$$
\text{Absolute Area Error} = |A_{\text{predicted}} - A_{\text{ground truth}}|
$$

$$
\text{Percent Area Error} =
\frac{|A_{\text{predicted}} - A_{\text{ground truth}}|}
{A_{\text{ground truth}}}
\times 100
$$

- **Purpose:** Measures the difference between the predicted cell/colony area and the manually traced ground-truth area.
- Use pixels squared ($px^2$) before calibration, or square micrometers ($\mu m^2$) after calibration.
- Lower values indicate more accurate area measurements.

### Equivalent Diameter Error

The equivalent diameter is the diameter of a circle with the same area as the measured cell or colony.

$$
D_{\text{equivalent}} = 2\sqrt{\frac{A}{\pi}}
$$

$$
\text{Absolute Equivalent Diameter Error} =
|D_{\text{predicted}} - D_{\text{ground truth}}|
$$

$$
\text{Percent Equivalent Diameter Error} =
\frac{|D_{\text{predicted}} - D_{\text{ground truth}}|}
{D_{\text{ground truth}}}
\times 100
$$

- **Purpose:** Compares predicted and manually measured cell/colony size using one intuitive length measurement.
- Use pixels ($px$) before calibration, or micrometers ($\mu m$) after calibration.
- Lower values indicate more accurate size measurements.

## My Dataset
My dataset is publicly accessible via Roboflow here: 
https://app.roboflow.com/greenlabcells/greenlab-dataset/train




