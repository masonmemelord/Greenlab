# FASTAPI imports
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.imaging import read_plane
from time import perf_counter
import logging
import os
from pydantic import BaseModel
from PIL import Image
import io, base64, numpy as np, cv2, bcrypt
import json 
from pathlib import Path
from tempfile import TemporaryDirectory
from app.measurement.cell_sizer import IMAGE_EXTENSIONS, measure_image
from app.detection.yolo_detector import CellDetector
from typing import List
def get_database():
    # Image tools can start even when authentication storage is not configured.
    try:
        from app.db import supabase
        return supabase
    except Exception as error:
        logging.exception("Database initialization failed")
        raise HTTPException(503, "Authentication database is unavailable. Check backend configuration.") from error



app = FastAPI()

# Middleware access, will pull from frontend domain and link
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "https://greenlab-frontend.vercel.app,http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep the production model path independent of the command's working directory.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
detector = None
colony_detector = None


def get_detector(colony=False):
    global detector, colony_detector
    cached = colony_detector if colony else detector
    if cached is None:
        weights = BACKEND_ROOT / "ml" / "weights" / ("segmentation" if colony else "detection") / "best.pt"
        if not weights.is_file():
            raise HTTPException(503, "Colony segmentation weights are missing. Train with ROI labels first." if colony else "Cell detection weights are missing on the backend.")
        try:
            cached = CellDetector(model_path=weights)
        except Exception as error:
            logging.exception("Model initialization failed")
            raise HTTPException(503, "Model could not load. Check backend logs and dependencies.") from error
        if colony:
            if cached.model.task != "segment":
                raise HTTPException(503, "Colony weights must be a segmentation model.")
            colony_detector = cached
        else:
            detector = cached
    return cached


@app.post("/api/image-preview")
async def image_preview(file: UploadFile = File(...), page: int = Query(0, ge=0)):
    try:
        image, pages = read_plane(await file.read(), page)
    except (OSError, ValueError, EOFError) as error:
        raise HTTPException(400, f"Could not read {file.filename}: {error}") from error
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return Response(buffer.getvalue(), media_type="image/png", headers={"X-Image-Pages": str(pages)})


@app.post("/api/colony-detect")
async def colony_detect(file: UploadFile = File(...), page: int = Query(0, ge=0), confidence: float = Query(0.5, ge=0.1, le=0.9)):
    try:
        image, _ = read_plane(await file.read(), page)
    except (OSError, ValueError, EOFError) as error:
        raise HTTPException(400, f"Could not read {file.filename}: {error}") from error
    model = get_detector(colony=True)
    start = perf_counter()
    try:
        result = model.predict(image, confidence=confidence)
    except Exception as error:
        logging.exception("Colony inference failed")
        raise HTTPException(500, "Colony inference failed. Check backend logs.") from error
    polygons = [] if result.masks is None else [polygon.tolist() for polygon in result.masks.xy]
    return {"polygons": polygons, "elapsed_seconds": perf_counter() - start}

# Normalize image
def normalize_image(image):
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_array = clahe.apply(img_array)
    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(img_rgb)

# --- Auth ---
class Credentials(BaseModel):
    username: str
    password: str

@app.post("/api/signup")
def signup(creds: Credentials):
    supabase = get_database()
    # Check for Tulane email
    if not creds.username.endswith('@tulane.edu'):
        raise HTTPException(status_code=400, detail="Only Tulane email addresses are allowed")

    # Check if user already exists
    result = supabase.table("users").select("username").eq("username", creds.username).execute()
    if result.data:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash and store password
    hashed = bcrypt.hashpw(creds.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    supabase.table("users").insert({"username": creds.username, "password": hashed}).execute()

    return {"message": "Account created"}

@app.post("/api/login")
def login(creds: Credentials):
    supabase = get_database()
    # Fetch user from Supabase
    result = supabase.table("users").select("password").eq("username", creds.username).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check hashed password
    stored = result.data[0]["password"]
    if isinstance(stored, str):
        stored = stored.encode('utf-8')
    if not bcrypt.checkpw(creds.password.encode('utf-8'), stored):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}

# --- Detection ---
@app.post("/api/detect")
async def detect(
    files: List[UploadFile] = File(...),
    confidence: float = Query(0.5, ge=0.1, le=0.9),
    page: int = Query(0, ge=0),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    model = get_detector()
    results_out = []

    for file in files: #Runs loop to allow for "unlimited" file selection
        try:
            image, pages = read_plane(await file.read(), page)
        except (OSError, ValueError, EOFError) as error:
            raise HTTPException(400, f"Could not read {file.filename}: {error}") from error

        start = perf_counter()
        normalized = normalize_image(image) #normalizes images -> greyscale
        try:
            results = model.predict(normalized, confidence=confidence)
        except Exception as error:
            logging.exception("Detection failed")
            raise HTTPException(500, "Detection failed. Check backend logs for the model error.") from error
        elapsed = perf_counter() - start

        annotated = results.plot()
        success, buffer = cv2.imencode('.jpg', annotated)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Could not encode result image for {file.filename}"
            )

        results_out.append({
            "filename": file.filename,
            "cell_count": len(results.boxes),
            "page": page + 1,
            "pages": pages,
            "elapsed_seconds": elapsed,
            "image": base64.b64encode(buffer).decode("utf-8")
        })

    return {"results": results_out, "total_files": len(results_out)}

@app.post("/api/cell-measure")
async def cell_measure(files: List[UploadFile] = File(...),
                       sensitivity: float = Query(0.5, ge=0.0, le=1.0),
                       cell_darker_than_bg: bool = Query(False),
                       min_diameter_um: float = Query(3.0, gt=0),
                       max_diameter_um: float = Query(100.0, gt=0),
                       split_touching_cells: bool = Query(True),
                       h_min: float = Query(2.0, ge=0),
                       um_per_px: float | None = Query(None, gt=0),
                       page: int = Query(0, ge=0),):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if max_diameter_um <= min_diameter_um:
        raise HTTPException(status_code=422, detail="Maximum diameter must be larger than minumun diameter.")
    
    results_out = []

    with TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        for index, file in enumerate(files):
            filename = Path(file.filename or "upload").name
            suffix = Path(filename).suffix.lower()

            if suffix not in IMAGE_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"{filename} is not a supported image type.",
                )

            temp_path = temp_dir_path / f"{index}.png"
            try:
                image, _ = read_plane(await file.read(), page)
                image.save(temp_path)
            except (OSError, ValueError, EOFError) as error:
                raise HTTPException(400, f"Could not read {filename}: {error}") from error

            try:
                cells = measure_image(
                    temp_path,
                    sensitivity=sensitivity,
                    cell_darker_than_bg = cell_darker_than_bg,
                    min_diameter_um=min_diameter_um,
                    max_diameter_um=max_diameter_um,
                    split_touching_cells=split_touching_cells,
                    h_min=h_min,
                    um_per_px = um_per_px,
                )
            except (OSError, ValueError) as error:
                raise HTTPException(status_code=400, 
                detail=f"Could not measure {filename}: {error}",) from error

            #DataFrame.to_json converts NumPy values and NaN safely for JSON.
            cell_records = json.loads(cells.to_json(orient="records"))

            results_out.append({
                "filename": filename,
                "cell_count": len(cells),
                "cells": cell_records,
                "is_calibrated": um_per_px is not None,
            })

    return {
        "results": results_out,
        "total_files": len(results_out),
        "total_cells": sum(item["cell_count"] for item in results_out),
    }


            
