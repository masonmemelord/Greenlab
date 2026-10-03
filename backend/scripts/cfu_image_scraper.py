"""
CFU Colony Image Scraper — PMC FTP Package Method
==================================================
Scrapes open-access paper figures for hematopoietic CFU subtypes:
    CFU-E, CFU-G, CFU-GM, CFU-GEMM, CFU-M, BFU-E

Pipeline:
    1. Search PubMed for open-access papers per cell type
    2. Look up each PMCID in PMC's OA Web Service to get its FTP .tar.gz URL
    3. Download and extract the tar package (contains XML + all images)
    4. Copy image files into per-subtype folders
    5. Write a CSV manifest (paper, filename, cell type)

Dependencies:
    pip install biopython requests tqdm

Usage:
    python scripts/cfu_image_scraper.py
    python scripts/cfu_image_scraper.py --cell_type "CFU-GM" --max_papers 30
"""

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import os
import re
import csv
import time
import tarfile
import shutil
import argparse
import requests
import tempfile
from pathlib import Path
from tqdm import tqdm
from Bio import Entrez

# ── Configuration ─────────────────────────────────────────────────────────────

Entrez.email = "mmitchell7@tulane.edu"   # REQUIRED by NCBI — change this

BACKEND_ROOT  = Path(__file__).resolve().parents[1]
OUTPUT_DIR    = BACKEND_ROOT / "ml" / "datasets" / "raw" / "cfu_images"
MANIFEST_CSV  = OUTPUT_DIR / "manifest.csv"
REQUEST_DELAY = 1.5                        # Seconds between requests
MAX_PAPERS    = 50                         # Papers per cell type

# Image file extensions to extract from tar packages
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# Caption keywords that indicate a microscopy/colony image
# Any figure whose caption contains at least one of these passes the filter
CAPTION_KEYWORDS = [
    "colon",        # colony, colonies
    "cfu",          # CFU-E, CFU-GM etc.
    "bfu",          # BFU-E
    "microscop",    # microscopy, microscopic
    "magnif",       # magnification
    "dish",         # culture dish
    "culture",      # cell culture
    "erythroid",
    "progenitor",
    "hematopoiet",  # hematopoietic, hematopoiesis
    "methylcellulose",
    "methocult",
    "stain",        # stained colonies
    "burst",        # BFU-E burst colonies
]

# Cell types → PubMed search queries
CELL_TYPES = {
    "CFU-E":    'CFU-E[tiab] OR "erythroid colony"[tiab] AND "open access"[filter]',
    "BFU-E":    'BFU-E[tiab] OR "burst forming unit erythroid"[tiab] AND "open access"[filter]',
    "CFU-G":    'CFU-G[tiab] OR "granulocyte colony forming"[tiab] AND "open access"[filter]',
    "CFU-M":    'CFU-M[tiab] OR "monocyte colony forming"[tiab] AND "open access"[filter]',
    "CFU-GM":   'CFU-GM[tiab] OR "granulocyte macrophage colony"[tiab] AND "open access"[filter]',
    "CFU-GEMM": 'CFU-GEMM[tiab] OR "multipotent progenitor colony"[tiab] AND "open access"[filter]',
}

# PMC OA Web Service — returns FTP download URL for a given PMCID
OA_SERVICE_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"


# ── Step 1: Search PubMed for PMCIDs ──────────────────────────────────────────

def search_pmc(query: str, max_results: int) -> list[str]:
    """
    Returns a list of PMCIDs for open-access papers matching the query.
    """
    handle = Entrez.esearch(
        db="pmc",
        term=query,
        retmax=max_results,
        usehistory="y"
    )
    record = Entrez.read(handle)
    handle.close()
    return record.get("IdList", [])


# ── Step 2: Get FTP tar.gz URL from PMC OA Web Service ───────────────────────

def get_ftp_url(pmcid: str) -> str | None:
    """
    Queries the PMC OA Web Service for a given PMCID.
    Returns the FTP .tar.gz download URL, or None if not available.

    Example response URL:
        ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/8e/71/PMC5334499.tar.gz
    We convert ftp:// to https:// so requests can handle it.
    """
    params = {"id": f"PMC{pmcid}"}

    try:
        resp = requests.get(OA_SERVICE_URL, params=params, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [WARN] OA service failed for PMC{pmcid}: {e}")
        return None

    # Parse the tgz link out of the XML response
    # Format: <link format="tgz" href="ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/.../PMCXXXXX.tar.gz"/>
    match = re.search(r'format="tgz"[^>]*href="([^"]+)"', resp.text)
    if not match:
        return None

    ftp_url = match.group(1)

    # Convert ftp:// to https:// — requests doesn't support raw FTP
    https_url = ftp_url.replace("ftp://", "https://", 1)
    return https_url


# ── Step 3a: Caption keyword filter ──────────────────────────────────────────

def caption_passes_filter(caption: str) -> bool:
    """
    Returns True if the figure caption contains at least one microscopy/colony
    keyword. Case-insensitive. Figures with no caption are rejected by default
    since we can't verify what they show.
    """
    if not caption.strip():
        return False  # No caption — skip, can't verify content

    caption_lower = caption.lower()
    return any(keyword in caption_lower for keyword in CAPTION_KEYWORDS)


def build_caption_map(extract_dir: Path) -> dict[str, str]:
    """
    Reads the XML file from an extracted PMC package and builds a mapping of:
        image_filename (no extension) → figure caption text

    This lets us look up the caption for any image file found in the package.
    """
    caption_map = {}

    # Find the XML file in the extracted directory
    xml_files = list(extract_dir.rglob("*.xml"))
    if not xml_files:
        return caption_map

    xml_text = xml_files[0].read_text(encoding="utf-8", errors="ignore")

    # Extract all <fig> blocks from the XML
    fig_blocks = re.findall(r'<fig\b[^>]*>(.*?)</fig>', xml_text, re.DOTALL)

    for block in fig_blocks:
        # Get image filename from graphic href
        href_match = re.search(r'xlink:href="([^"]+)"', block)
        if not href_match:
            continue
        # Strip path and extension to use as lookup key
        img_key = Path(href_match.group(1)).stem.lower()

        # Get caption text and strip XML tags
        caption_match = re.search(r'<caption>(.*?)</caption>', block, re.DOTALL)
        if caption_match:
            raw_caption = re.sub(r'<[^>]+>', ' ', caption_match.group(1))
            caption_map[img_key] = " ".join(raw_caption.split())

    return caption_map


# ── Step 3b: Download and extract tar package, return filtered image paths ────

def extract_images_from_tar(tar_url: str, pmcid: str) -> list[Path]:
    """
    Downloads the .tar.gz package for an article, extracts it to a temp
    directory, and returns paths to image files that pass the caption filter.
    Cleans up the tar file after extraction.
    """
    image_paths = []

    try:
        resp = requests.get(tar_url, timeout=60, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [WARN] Download failed for PMC{pmcid}: {e}")
        return []

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        extract_dir = tmp_path.parent / f"pmc_{pmcid}"
        extract_dir.mkdir(exist_ok=True)

        with tarfile.open(tmp_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)

        # Build caption lookup from the XML in this package
        caption_map = build_caption_map(extract_dir)

        # Collect images that pass the caption filter
        for f in extract_dir.rglob("*"):
            if f.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            # Look up caption using the image filename stem as key
            img_key = f.stem.lower()
            caption = caption_map.get(img_key, "")

            if caption_passes_filter(caption):
                image_paths.append(f)
            # else: silently skip — not a colony/microscopy figure

    except (tarfile.TarError, Exception) as e:
        print(f"    [WARN] Extraction failed for PMC{pmcid}: {e}")

    finally:
        tmp_path.unlink(missing_ok=True)

    return image_paths


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(cell_types: dict, max_papers: int):
    OUTPUT_DIR.mkdir(exist_ok=True)

    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["cell_type", "pmcid", "filename", "caption", "source_url"])
        writer.writeheader()

        for cell_type, query in cell_types.items():
            print(f"\n{'='*60}")
            print(f"Cell type: {cell_type}")

            # Create output subfolder for this cell type
            folder = OUTPUT_DIR / cell_type.replace("-", "_")
            folder.mkdir(exist_ok=True)

            # Step 1: Search PMC
            print(f"  Searching PubMed Central (max {max_papers} papers)...")
            pmcids = search_pmc(query, max_papers)
            print(f"  Found {len(pmcids)} papers")
            time.sleep(REQUEST_DELAY)

            total_saved = 0

            for pmcid in tqdm(pmcids, desc=f"  {cell_type} papers"):

                # Step 2: Get FTP tar.gz URL
                tar_url = get_ftp_url(pmcid)
                time.sleep(REQUEST_DELAY)

                if not tar_url:
                    continue  # Paper not in OA subset — skip

                # Step 3: Download + extract images
                image_paths = extract_images_from_tar(tar_url, pmcid)
                time.sleep(REQUEST_DELAY)

                # Copy each image into the cell type folder
                for img_path in image_paths:
                    dest_filename = f"PMC{pmcid}_{img_path.name}"
                    dest_path = folder / dest_filename

                    if not dest_path.exists():
                        shutil.copy2(img_path, dest_path)

                    # Look up caption for manifest using image stem as key
                    caption_map = build_caption_map(
                        Path(tempfile.gettempdir()) / f"pmc_{pmcid}"
                    )
                    caption = caption_map.get(img_path.stem.lower(), "")

                    total_saved += 1
                    writer.writerow({
                        "cell_type":  cell_type,
                        "pmcid":      pmcid,
                        "filename":   str(dest_path),
                        "caption":    caption,
                        "source_url": tar_url,
                    })

                # Clean up temp extract directory
                extract_dir = Path(tempfile.gettempdir()) / f"pmc_{pmcid}"
                if extract_dir.exists():
                    shutil.rmtree(extract_dir, ignore_errors=True)

            print(f"  Saved {total_saved} images → {folder}")

    print(f"\nDone. Manifest written to: {MANIFEST_CSV}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape CFU colony images from PubMed Central")
    parser.add_argument("--cell_type",  type=str, default=None,
                        help="Single cell type to scrape (e.g. 'CFU-GM'). Default: all.")
    parser.add_argument("--max_papers", type=int, default=MAX_PAPERS,
                        help=f"Max papers per cell type (default: {MAX_PAPERS})")
    args = parser.parse_args()

    targets = CELL_TYPES
    if args.cell_type:
        if args.cell_type not in CELL_TYPES:
            print(f"Unknown cell type '{args.cell_type}'. Choose from: {list(CELL_TYPES.keys())}")
            exit(1)
        targets = {args.cell_type: CELL_TYPES[args.cell_type]}

    run(targets, args.max_papers)
