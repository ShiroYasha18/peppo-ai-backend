import os
import tempfile
import requests
import replicate
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# Option 2: Update the backend to look for the .env file in the parent directory


import os
import tempfile
import requests
import replicate
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(dotenv_path="../.env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN not found in environment variables. Check your .env file.")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Pydantic model for request validation
class VideoGenerationRequest(BaseModel):
    api_key: Optional[str] = None
    prompt: str
    fps: Optional[int] = 24
    duration: Optional[int] = 5
    resolution: Optional[str] = "720p"
    aspect_ratio: Optional[str] = "16:9"
    camera_fixed: Optional[bool] = False

@app.post("/generate")
async def generate_video(request: VideoGenerationRequest):
    # Validate that prompt exists and is not empty
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    prompt = request.prompt.strip()
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Check if prompt is too short (minimum 3 characters)
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Prompt must be at least 3 characters long")
    
    # Use the parameters from the frontend request
    input_data = {
        "fps": request.fps or 24,
        "prompt": prompt,
        "duration": request.duration or 5,
        "resolution": request.resolution or "720p",
        "aspect_ratio": request.aspect_ratio or "16:9",
        "camera_fixed": request.camera_fixed or False
    }
    
    try:
        # Use replicate.run
        output = replicate.run(
            "bytedance/seedance-1-lite",
            input=input_data
        )
        
        # Handle both string and object outputs
        if isinstance(output, str):
            video_url = output
        elif hasattr(output, 'url') and callable(output.url):
            video_url = output.url()
        elif hasattr(output, 'url'):
            video_url = output.url
        else:
            video_url = str(output)
        
        return {
            "video_url": video_url,
            "message": "Video generated successfully",
            "prompt_used": prompt,
            "duration": f"{request.duration or 5} seconds",
            "resolution": request.resolution or "720p",
            "fps": request.fps or 24,
            "aspect_ratio": request.aspect_ratio or "16:9",
            "camera_fixed": request.camera_fixed or False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@app.post("/generate-download")
async def generate_and_download_video(request: Request):
    data = await request.json()
    
    # Validate that prompt exists and is not empty
    if "prompt" not in data:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    prompt = data["prompt"].strip()
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Check if prompt is too short (minimum 3 characters)
    if len(prompt) < 3:
        raise HTTPException(status_code=400, detail="Prompt must be at least 3 characters long")
    
    input_data = {
        "fps": 24,
        "prompt": prompt,
        "duration": 5,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "camera_fixed": False
    }
    
    try:
        # Use replicate.run
        output = replicate.run(
            "bytedance/seedance-1-lite",
            input=input_data
        )
        
        # Download the video file
        if isinstance(output, str):
            video_url = output
        elif hasattr(output, 'url') and callable(output.url):
            video_url = output.url()
        elif hasattr(output, 'url'):
            video_url = output.url
        else:
            video_url = str(output)
        
        # Download from URL
        response = requests.get(video_url)
        
        # Create a temporary file to store the video
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # Return the file as a download
        return FileResponse(
            path=temp_file_path,
            media_type="video/mp4",
            filename=f"generated_video_{prompt[:20]}.mp4"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Video Generation API is running!"}

# Add this at the end of main.py
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
