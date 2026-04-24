from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import shutil
import asyncio
from app.core.engine import AutomatedTrainingEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUTS_DIR = "outputs"
TEMP_DIR = "temp"
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

jobs = {}

async def run_training_engine(job_id, pdf_path):
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    original_filename = jobs[job_id].get("filename")
    try:
        def progress_cb(p, msg):
            jobs[job_id]["progress"] = p
            jobs[job_id]["message"] = msg

        engine = AutomatedTrainingEngine(
            pdf_path=pdf_path,
            output_dir=output_dir,
            progress_callback=progress_cb,
            original_filename=original_filename
        )
        # run engine (engine.run is async)
        video_path = await engine.run()
        
        jobs[job_id]["status"] = "completed"
        # Since we mount outputs/, the static link is:
        jobs[job_id]["video_url"] = f"/outputs/{job_id}/final_training.mp4"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@app.post("/process_default")
async def process_default(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    
    source_video = os.path.join(TEMP_DIR, "final_training (3).mp4")
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    dest_video = os.path.join(output_dir, "final_training.mp4")
    
    if os.path.exists(source_video):
        shutil.copyfile(source_video, dest_video)
        
    jobs[job_id] = {
        "status": "completed",
        "progress": 100,
        "message": "Video loaded from cache.",
        "video_url": f"/outputs/{job_id}/final_training.mp4",
        "error": None,
        "filename": "16. Validation SOP for Compressed Air-GAS Revision.03 130219 (1).pdf"
    }
    
    return {"job_id": job_id, "status": "processing"}

@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())[:8]
    pdf_path = os.path.join(TEMP_DIR, f"{job_id}.pdf")
    
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    jobs[job_id] = {
        "status": "processing", 
        "progress": 0, 
        "message": "Starting engine...", 
        "filename": file.filename
    }
    
    # We must use a wrapper to run the async function in background
    background_tasks.add_task(run_training_engine, job_id, pdf_path)
    
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
