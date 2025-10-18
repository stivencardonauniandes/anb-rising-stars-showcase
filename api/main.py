import logging
import os
import shutil
import requests
import uvicorn

from pydantic import BaseModel
from fastapi.params import Form
from routers import auth, public
from schemas.pydantic_schemas import VideoUploadResponse
from moviepy.editor import VideoFileClip
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Constants
API_TITLE = "ANB Rising Stars Showcase API"
INVALID_FILE_TYPE = "Tipo de archivo inválido. Se requiere un archivo de video."
INVALID_VIDEO_LENGTH = "El video debe tener una duración entre 20 y 60 segundos."
INVALID_VIDEO_RESOLUTION = "La resolución del video debe ser al menos 1080p."
INVALID_VIDEO_TITLE = "El título del video no puede estar vacío."
FILE_PROCESSING_ERROR = "Error al procesar el archivo de video."
FILE_UPLOAD_SUCCESS = "Video subiddo correctamente. Procesamiento en curso."

# Configure logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title=API_TITLE,
    description="API for the ANB Rising Stars Showcase application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(public.router)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    message: str
    service: str = API_TITLE

# Health Check Routes
@app.get("/api/health", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="success", 
        message=f"{API_TITLE} is running!",
        service=API_TITLE
    )


# Endpoint to upload videos
@app.post("/api/videos/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...), title: str = Form(...)):

    # Validate title
    if not title or title.strip() == "":
        raise HTTPException(status_code=400, detail=INVALID_VIDEO_TITLE)
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail=INVALID_FILE_TYPE)
    
    # Create a temporary file path
    temp_filepath = f"temp_video_{file.filename}"

    # Save the uploaded file to the temporary path
    with open(temp_filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Validate video length and resolution
        video_clip = VideoFileClip(temp_filepath)
        duration = video_clip.duration  # Duration in seconds
        video_clip.close()
        if duration < 20 or duration > 60:  # Duration must be between 20 and 60 seconds
            raise HTTPException(status_code=400, detail=INVALID_VIDEO_LENGTH)   
        
        # Upload video to Nextcloud - open the temp file to read it
        with open(temp_filepath, "rb") as video_file:
            upload_video_to_nextcloud(video_file, title)
        return VideoUploadResponse(
            message=FILE_UPLOAD_SUCCESS,
            task_id='1234'
        )
    except (ValueError, BufferError, RuntimeError) as e:
        logger.error(f"Error processing video file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=FILE_PROCESSING_ERROR)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
    

def upload_video_to_nextcloud(file: File, filename: str) -> str:
        """
        Function to upload video to Nextcloud.
        Return the url of the uploaded video.
        """
        try:
            webdav_url = "http://nextcloud"
            username = "worker"
            password = "super-secret"
            remote_path = f"/raw/{filename}"
            remote_path_url = webdav_url + f"/remote.php/dav/files/worker/{remote_path}"
            response = requests.put(
                remote_path_url,
                data=file,
                auth=(username, password)
            )
            if response.status_code not in [200, 201, 204]:
                logger.error(f"Failed to upload video to Nextcloud: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Failed to upload video to storage service.")
            return remote_path
        except Exception as e:
            logger.error(f"Failed to upload video to Nextcloud: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload video to storage service.")

    # Upload video to Nextcloud (placeholder function)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
