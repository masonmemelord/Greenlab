# TUCellDetection-Yolov12
This is the repository for training the Tulane Cell Detection App using YOLO v12

# LOGS + WHAT IM LEARNING
## Feb 10: 
Today I've made a fair share of progress. Over the past weeks I've been downloading and setting the stage for the actual programming. I've learned some basics of Streamlit, SQL, and bcrypt. Claude AI has been very helpful for me understanding the syntax rules. I know Claude and generative AI is frowned on, but considering my classload, it's made learning very efficient.

### Some Quantifiable Progress
- Built a login_user() that connects to streamlit's and SQL's database. Depending on input by user, login_user() fetches the info and closes the page
- Built a signup_user() that does similar work. A lot more extensicve due to the new table needing to be committed, as well as password hashing. Finally a button is used to connect to database, passwords are hashed, usernames are crossrefrenced to prevent duplication.

### Next Goals
- Update Database
- Link to actual cell detection interface
- Implement functionality

## Feb 11: 
I finished the sign-in/sign-up portion of the app. I've also been able to get a pretty firm CONCEPTUAL understanding of SQL. Bcrypt on the other hand is a tad bit more challenging. As far as it's been used I think it's been for utf encoding gates. I plan on adding more comments on my code later tonight. I'm working hard to make sure I understand everything that I'm working with AI to make (which has made hand typing this a lot more time consuming). Streamlit is super fun. It works similar to TSX. I dont really understand how developers understand all these commands on-hand though >o<

### Some Quantifiable Progress
- Revamped the login/signup page by implementing functionality in tabs (formerly were seperate methods)
- Built the image uploading service
- Added QOL updates to login/signup page

### Next Goals
- Consolidation of database
- Inquire about AI trainers:   
    - Training AI if needed
- Start getting baseline information for network/database linkage to TU network.

## Feb 14: 
I shouldn't have taken this 3 day break, but hey midterms are hard. Today I didn't do as much as I did earlier this week (but this could be in part because of there being less to do). But circling to the actual project, it was more of the same today. the only difficult thing was understanding cv2. From what I understand, and what has been explained, cv2 works by translating images to arrays. Images are just RGB number grids and when they're normalized (like in this case), the values are translated to the respective color-stripped values. From there detection begins and are reverted back to their original color. At first I was using PIL ImageOps, which was holistically translating the image, but I switched to cv2 in order to maintain image fidelity. The last thing (and probably most tedious) is to self train this AI on Roboflow, which i have to do manually.

### Some Quantifiable Progress
- Added button to image uploader
- Added image normalizer
- Currently training AI on Roboflow

### Next Goals
- Finish AI training
- Continue goals from Feb 11th

## Feb 18: 
I figured out I may be using the wrong yolo model (yolov8n). After meeting with my professor, we settled on the yolov12 model for accuracy. Once I get that crossed over, I need to find the specific submodel of YOLO that I need. I'll probably start coding tomorrow.

### Some Quantifiable Progress
- N/A

### Next Goals
- Change AI model
- Find out how to print metadata

## Feb 22: 
I just spent 3 hours trying to integrate yolov12 just to figure its running on a version of python (3.11, I'm running 3.13) not viable to release for a fleshed out app. Very frustrating night. I had to move everything back. Pretty upsetting. Yolov8 isn't as accurate. Thinking about training it myself via Roboflow. Hate this plateau going on. I'm going to focus on metadata tomorrow so I can just hone in on the model accuracy :/. Nonetheless, I'm remaining determined (God is good).

### Some Quantifiable Progress
- N/A

### Next Goals
- Find out how to print metadata
- Find Ultralytics most accurate version of yolov8

## Feb 24: 
Quick hour session on understanding, printing, and downloading metadata. From what I understand, bounding boxes are key to determining size (which is almost obvious). I also use pandas dataframes to show/store the data. The next steps are to maximize this yolov8 and set detection names. Im pretty sure cell clusters are not named cake, teddy bear, and tennis ball. I know this could be done in hours with AI, but im trying to learn it the right way (hence these updates).

### Some Quantifiable Progress
- Printed metadata
- Made metadata downloadable

### Next Goals
- Find Ultralytics most accurate version of yolov8
- Set detection names of images

## Feb 25: 
Nothing much to update. I implemented a dictionary and linked it to detection.py. I really hope i wouldn't have to manually train the AI, but here I am a week later, doing what I didn't want to do. I already have Roboflow set up, so the next step is getting more images to train it with and link it to yolov8n (via my to-be training script in train.py). I only have premium for a couple more days, so I have to make the best of it. I'll probably email one of my "clients" for more labeled images. God know's I'm not going to mixing and matching cluster types.

### Some Quantifiable Progress
- Made dictionary to prepare for implementation of image dataset

### Next Goals
- Trace dataset via Roboflow
- Write script to point to detection.py

## Mar 21: 
Almost a month later but I'm back. Currently on break and completing an academic comeback, but I'm glad to be back. Ihad to make some slight changes with these couple files, mainly train.py. I implemented the Roboflow detection for basic testing. Although the picture batch is nowhere near enough, I'm glad its working (takes a long time to download though). The accuracy can use some work but that comes with adding mroe images. I'm kinda tired, I've ben doing this for about 2-3 hours on and off so I'll probably be more in detail next update (Sunday/Monday). The goal is to get this deployment ready by Easter. God is Great!

### Some Quantifiable Progress
- Connected Roboflow to train.py

### Next Goals
- Add around 100-200 more reference images
- Prepare for full deployment

## Mar 25: 
Sooo I def have been slacking. Seems like healthcare people are REALLY serious aboout sealing off blood cell cultures, no matter though, I had Claude build a scraper to find images from websites, of which i can download, label, and add to my Roboflow. I'm currently breaking down, and will breakdown in a subheader. I'll test everything tomorrow after BJJ. 

#### Script Logic Breadown (Block 1)
Block 1: passes in a search query from pre-defined dictionaries using a string and max_results to add to a string. From there handle is initialized a variable to search the pmc database, set the query to the term parameter, retmax to return the max_results, and use_history set to char literal of y, which searches the results on the server-side. record reads the handle and it is closed. Return the record of the getter which takes the parameters of the list as a safe dictionary lookup.

### Some Quantifiable Progress
- Generated a image scraper 

### Next Goals 
- Scrape images
- Add around 100-200 more reference images
- Prepare for full deployment

## Mar 26: 
Just broke down the rest of the script. Running everything tomorrow.

#### Script Logic Breadown (Block 2, 3, 4)
Block 2 uses the pmcid as a string. params takes in the database type, id, return type, and return mode. A try/catch (exempt in py) block is used for requesting from the PMC source website. xml is initializes as response text and figures is initialized as a list, which can take in multiple types of data. fig blocks  blocks in information from the PMC XML, which is done via a for loop that takes images from the href, which themselves are blocked together. The if conditional checks for real images using (jpg/jpeg/png.tif/tiff) as reference formats. the captions are also pulled and blocked to gather. all the information is then added and returned to the figures list under; url, caption, and figure id.

downloadImage takes in url as a string, dest_path as a path and returns the function as a boolean value. If the destination path exists then it is true and the file is already downloaded. the try/except block tries to get the url and raise it for HTTP status. It then verifies the type of the content (jpg/jpeg, png, tif, etc). If it isn't found it returns false. With a successful type it will set the dest type as f (possibly shorthand for file) and iterates a for loop using  the chunk size  to buffer write time. If nothing works it jump to the except case which will return False

The main pipeline defines a function names run using the cell_types dictionary and max papers int. opens the manifest CSV outside to write for the cell_type and query within the cell_types dictionary. A folder and subdivisions are then created to write the different cell types to once the search is completed. The search uses the query and max papers as parameters and initializes a counter for saved images. A for loop then goes over the ids and cell_type dictionary. A nested for loop is in that one and makes a safe filename and type and sets the destination path to the folder / filename. The download process is then set up which adds to the saved counter and writes to each row with the respective information (if True).


### Some Quantifiable Progress
- Generated a image scraper 

### Next Goals 
- Scrape images
- Add around 100-200 more reference images
- Prepare for full deployment

## Mar 27: 
The scraper did not work, but it was good pratice to read and understand the code. It ultimately returned the images but not in the way I wanted. I had to web surf for about 30 minutes to get some decent images. I found both pdfs from STEMCELL Technologies (WE LOVE scraping) which ironically this is a personalized version of. I was able to get around 171 more images so thats a big W. I'll be updating the database on Roboflow and the app and deleting the script tomorrow.

### Some Quantifiable Progress
- Found primary sources to scrape

### Next Goals 
- Annotate new images
- Update Database
- Prepare for full deployment (Almost Done!)

## Mar 27: 
Updated the datset, and everything is working!! Just not how expected. The detection seems to default to and/or over analyse towards BFU (Burst Forming Unit) colonies. Its definitely a Roboflow balance issue, so hopefully with soe input I can get this rebalanced correctly. Small fixes hopefully.

### Some Quantifiable Progress
- Everything works?

### Next Goals 
- Balance Database
- Prepare for full deployment

## Apr 6: 
Soooo I had to switch to FastAPI. This turned to a fullstack pretty quick. Luckily since all my logic was the same, the switch from Python to TS was pretty quick (i am not a fan of file hiearchy). Other than that I got to keep the backend the same, which means all frontend updates will be in the frontend folder and vice-versa.

### Some Quantifiable Progress
- Switched to React and Next.js

### Next Goals 
- Test everything
- Get in touch with Tulane IT
- Prepare for full deployment 

## Apr 7: 
Backend is slighty more complicated than frontend, still chill though. I just moved the dataset and linked it to the frontend. I have a feeling I may have to reimplement SQL for tabling, but we'll see.

### Some Quantifiable Progress
- Transferred Roboflow dataset

### Next Goals 
- Generate table reports
- Genereate downloadable images
- Build Navbar
- Prepare for full deployment

## May 14
Long time no see. I feel like at least once a month I'm making a major change to the functionality of this stack. Anyways, I switched to Supabase from SQLite3. From what I've seen and understand, Supabase handles concurrency better, as well the persistence problem with SQLite3. I hated having to update my dataset because I'd have to wait for hours for it to update. I added db.py to call Supabase. Also I have to update my weights on Roboflow, I was being dumb and didnt add any information for the test weights (explains why everything was CFU-GEMM and BFU-E).

### Some Quantifiable Progress
Switched from SQLite3 to Supabase

### Next Goals 
- Update dataset weights on Roboflow 

## May 16
Documentation after a long session is th worst but we gotta do it. Anyways the Supabase is fully operational and I have images detected at runtime. I was thinking about using RoboflowAPI, but that costs money (WE HATE THAT!). I kept changes local, updated the database and changed the weights.

### Some Quantifiable Progress
- Supabase fully operational
- Updated Roboflow database and weights

### Next Goals 
- Deployment on Vercel #softlaunch!

## May 18
Switched to Docker for Railway. I tried to used Nixpacks, but from what I understand, Nixpack works better for Railway but not necessarily OpenCV (Open-Source Computer Vision). Also Nixpacks was causing runtime errros because it couldn't find the right library to send OpenCV. By switching to Docker I was able to "override" the Nixpacks and talk directly to the OpenCV C++ libraries by . It also allows for faster caching after the intial build. The only "downside" is that I will have to understand Docker better the larger the dataset gets. Lastly I switched to numpy with wheels, which basically means its pre-compiled, think of it as a two-layer cake, they work together but work independently before coming together.

### Some Quantifiable Progress
- Switched to Docker from Nixpacks
- Put wheels on my numPy

### Next Goals 
- Deployment on Vercel #softlaunch!

## May 28
I'm back. Everything is working as expected, the only things now are improving QoL things and possibly expanding to a downloadable app. I'll probably dedicate tomorrow to downloading and updating the roboflow dataset.

### Some Quantifiable Progress
- Everything works

### Next Goals 
- Update dataset
- Implement multiple file upload
- Expansion to App/Play store 

## Aug 21
Almost 3 months... Jeez. Anyways some small changes before I start restructuring. I'm currently implementing manual detection. I took the matlab files Prof. Erin gave me and translated it to Python (thank you ChatGPT), rewrote it and tested it in the CLI. 

### Some Quantifiable Progress
- Backend files manual_colony_tracer.py and cell_sizer.py work in the CLI

### Next Goals
- add thresholding
- equivalent diameter measurements across files
- update dataset


## Aug 24
Finished linked the new Python files. They work as a backup to the CV detection since the current dataset isn't in-depth enough to prevent bias/bad data. I added some more features to strengthen manual detection such as cell splitting, boundary control, and unified tabling, so this should also help with cross referencing data in the case that CV/Manual detection has major discrepancies

## Quantifiable Progress
- Finished backend files for manual detection
- Unified table storage
- Cell splitting for detection


## Next Goals
- Connect frontend for backend files

## Aug 28
Today was about giving the app a real backup plan instead of acting like CV is always right. I translated the manual colony tracer and CellSizer logic from the MATLAB files Prof. Erin gave me into Python. The goal is not to replace the YOLO/CV detection; it is to have a second measurement path when the dataset is biased, a colony is hard to detect, or the two methods need to be cross-referenced.

The new logic recognizes `.tif` and `.tiff` alongside the regular image formats. `manual_colony_tracer.py` handles the manual side: it finds 5x TIFFs, loads a display-friendly image, turns a traced polygon into a mask, and calculates the colony area in pixels and microns. `cell_sizer.py` handles the more automated backup workflow: folder/image selection, magnification calibration, thresholding, separating touching cells, and returning one consistent table of measurements.

### Some Quantifiable Progress
- Added Python versions of the manual tracer and CellSizer measurement logic
- Added `.tif` / `.tiff` image detection
- Kept manual and automatic measurements in a common column format for easier comparison
- Kept this workflow independent from Supabase and the main detection database

### Next Goals
- Keep tuning thresholding and cell-splitting settings on real lab images
- Compare manual/CV measurements to find where the model is underperforming
- Keep the frontend manual tracer as a backup tool, not another required backend route

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

### Results
Experiment pending.

### Sources
- [Add relevant YOLO segmentation paper/documentation]
- [Add biomedical cell-segmentation paper]
- [Add morphology/measurement paper]

### Next Steps
- Establish baseline metrics for current YOLOv8 model
- Train first segmentation model
- Define test dataset
- Compare segmentation measurements against manual measurements