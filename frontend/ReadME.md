## Apr 6: 
Welcome to the frontend rundown. Did not expect this to turn fullstack but I should've expected since I am making an APP. On the brightside I get to go back to frontend dev, which is a dub. I'll be running down the logic further as the wek goes down.

### Some Quantifiable Progress
- Moved Streamlit to Fast API and TSX/React

### Next Goals 
- Test everything
- Get in touch with Tulane IT
- Prepare for full deployment

## Apr 7: 
Frontend consolidation is still going strong. I had to move some stuff around, mainly specifying for Tulane emails. It's late so I might be forgetting some stuff. I have to add tables and downloadable images as well as some QoL things

### Some Quantifiable Progress
- Specified some email parameters

### Next Goals 
- Generate table reports
- Genereate downloadable images
- Build Navbar
- Prepare for full deployment

## Apr 12: 
I made a decent amount of changes for the frontend. Mainly a navbar, downloadable tables (similar to the Streamlit archive). The rest of the changes were primarily aesthetic. I updated globals.css, but I need to set the stage for universal integration, most of the CSS is inline. I'm not the biggest fan of tailwind tho, I'm an unc. 

### Some Quantifiable Progress
- Downloadable tab;es
- Built navbar
- Basic links

### Next Goals 
- QoL additions
- Universal CSS integration

## May 14
Back again. I implemented universal CSS and a profile page.

### Some Quantifiable Progress
- Universal CSS
- Profile page with account deletion

### Next Goals 
- Idek twin

## May 16
The move to supabase is complete. I have backend and frontend working now. I do need to test repeated login just in case, but as of right now it works. I fixed the sign-in to call on login so peopledont have to manually rememeber login. 

### Some Quantifiable Progress
- Supabase on frontend/backend

### Next Goals 
- Deployment on Vercel

## May 19
Just backtested for everything on the fullstack. I believe we are good to go!. I had to mess with some of the SQL and Supabase to handle profile changes. Before I was using a local flag to replace Supabase, but I wasn't really editing any database info. I wanted to make an app that didn't necessarily rely on internet, but logically in a research lab internet isn't an issue. I had to make a route file for deletion, updates, etc.

### Some Quantifiable Progress
- Full Supabase interactivity 

### Next Goals 
- Deployment on Vercel

## Jun 19
Here for documentation purposes. I have to handle grids in images before detection.

### Next Goals 
- Update grids + Redeploy

## Aug 24
Next plans are to update the page with manual detection. AI/CV detection will remain, manual will just be a fallback.

### Next Goals
- connect backend files 

## Aug 28
Manual detection is now visible from the dashboard instead of being a backend-only idea. I added a Manual Tracer link in the navbar that opens its own page, so the normal AI/CV workflow can stay clean while there is still a clear fallback when the model is not confident or the data looks off.

The tracer stays on the frontend by design. A user uploads PNG, JPG, JPEG, or TIFF images, traces a colony directly on the image, and the page converts the outline into area and equivalent-diameter measurements using a microns-per-pixel calibration. Nothing from this workflow needs to be sent to Supabase or a new backend route. Measurements live in the browser until the user downloads the CSV, which makes it useful for checking CV results without putting the current database architecture at risk.

### Some Quantifiable Progress
- Added a dashboard link to the standalone Manual Tracer page
- Added multi-image manual tracing with redraw, no-colony, and saved-trace options
- Added calibration-based area and equivalent-diameter measurements
- Added CSV download for manual measurements
- Added `.tif` / `.tiff` to the accepted upload types

### Next Goals
- Test manual tracing against a few known colony measurements
- Compare manual CSV results with CV results when the dataset produces questionable detections
- Keep improving the UI without forcing the backup workflow into the normal detection route

