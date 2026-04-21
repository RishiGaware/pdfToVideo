from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
import os
from processor import process_pdf_to_video

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job state
jobs = {}

# Ensure directories exist
OUTPUTS_DIR = "outputs"
TEMP_DIR = "temp"
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Mount outputs so video is accessible via URL
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

def run_job(job_id, pdf_path):
    output_dir = os.path.join(OUTPUTS_DIR, job_id)
    try:
        def update_progress(p):
            jobs[job_id]["progress"] = p
            
        video_path = process_pdf_to_video(pdf_path, output_dir, job_id, update_progress)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["video_url"] = f"/outputs/{job_id}/final.mp4"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@app.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())[:8]
    pdf_path = os.path.join(TEMP_DIR, f"{job_id}.pdf")
    
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    jobs[job_id] = {"status": "processing", "progress": 0, "filename": file.filename}
    background_tasks.add_task(run_job, job_id, pdf_path)
    
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
