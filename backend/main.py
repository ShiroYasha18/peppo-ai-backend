import os
import tempfile
import requests
import replicate
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import asyncio
from asyncio import Queue, Task
from functools import wraps
import time
import logging
import urllib.request
from urllib.parse import urlparse
import ffmpeg
import random

# Load .env from current directory
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request queue management system
class RequestQueueManager:
    def __init__(self, max_concurrent=5, max_queue_size=100):
        self.queue = Queue(maxsize=max_queue_size)
        self.max_concurrent = max_concurrent
        self.active_tasks = set()
        self.task_semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = {
            "total_processed": 0,
            "total_queued": 0,
            "total_errors": 0,
            "avg_processing_time": 0,
        }
        # Start the worker
        asyncio.create_task(self.worker())
    
    async def add_task(self, coro, *args, **kwargs):
        # Create a future to track the result
        result_future = asyncio.Future()
        
        # Put the task in the queue
        await self.queue.put((coro, args, kwargs, result_future))
        self.stats["total_queued"] += 1
        
        # Return the future so caller can await it
        return result_future
    
    async def worker(self):
        while True:
            # Get a task from the queue
            coro, args, kwargs, result_future = await self.queue.get()
            
            # Process the task with semaphore to limit concurrency
            asyncio.create_task(self._process_task(coro, args, kwargs, result_future))
    
    async def _process_task(self, coro, args, kwargs, result_future):
        async with self.task_semaphore:
            task_start = time.time()
            try:
                # Execute the coroutine
                task = asyncio.create_task(coro(*args, **kwargs))
                self.active_tasks.add(task)
                result = await task
                
                # Set the result in the future
                result_future.set_result(result)
                self.stats["total_processed"] += 1
                
                # Update average processing time
                processing_time = time.time() - task_start
                self.stats["avg_processing_time"] = (
                    (self.stats["avg_processing_time"] * (self.stats["total_processed"] - 1) + processing_time) / 
                    self.stats["total_processed"]
                )
                
            except Exception as e:
                # Set the exception in the future
                result_future.set_exception(e)
                self.stats["total_errors"] += 1
                logger.error(f"Task error in queue: {e}")
            finally:
                # Remove the task from active tasks
                if 'task' in locals():
                    self.active_tasks.remove(task)
    
    def get_stats(self):
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "active_tasks": len(self.active_tasks)
        }

# Initialize the queue manager
request_queue = RequestQueueManager(max_concurrent=5)

# Decorator for queueing endpoint handlers
def queued_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Add the task to the queue and wait for result
        return await request_queue.add_task(func, *args, **kwargs)
    return wrapper

# Environment variables
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN not found in environment variables. Check your .env file.")
if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    raise ValueError("Twilio credentials not found in environment variables.")

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Global state management
conversation_state = {}
user_preferences = {}

# Default video settings
DEFAULT_SETTINGS = {
    'aspect_ratio': '1:1',
    'resolution': '480p',
    'fps': 24,
    'duration': 5
}

# Pydantic models
class VideoGenerationRequest(BaseModel):
    prompt: str
    fps: Optional[int] = 24
    duration: Optional[int] = 5
    resolution: Optional[str] = "480p"
    aspect_ratio: Optional[str] = "1:1"

# Content moderation function (simplified without OpenAI for now)
async def moderate_content(text: str):
    """Simple content moderation - can be enhanced with OpenAI later"""
    # Basic keyword filtering
    inappropriate_keywords = ['violence', 'hate', 'explicit', 'harmful']
    text_lower = text.lower()
    
    for keyword in inappropriate_keywords:
        if keyword in text_lower:
            return False, f"Content contains inappropriate keyword: {keyword}"
    
    return True, "Content is appropriate"

# Settings parser function
def parse_settings_command(message: str):
    """Parse settings commands like '/settings ratio 16:9' or '/settings resolution=480p fps=24'"""
    parts = message.split()
    if len(parts) < 2:
        return None
    
    # Remove '/settings' from the beginning
    settings_parts = parts[1:]
    updates = {}
    
    for part in settings_parts:
        # Handle key=value format
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.lower().strip()
            value = value.strip()
            
            if key in ['aspect_ratio', 'ratio'] and value in ['16:9', '9:16', '1:1', '4:3']:
                updates['aspect_ratio'] = value
            elif key == 'resolution' and value in ['480p', '720p', '1080p']:
                updates['resolution'] = value
            elif key == 'fps' and value.isdigit():
                fps_val = int(value)
                if fps_val in [24, 30, 60]:
                    updates['fps'] = fps_val
            elif key in ['duration', 'time'] and value.isdigit():
                duration_val = int(value)
                if duration_val in [3, 5, 10]:
                    updates['duration'] = duration_val
        
        # Handle old format: '/settings ratio 16:9'
        elif len(settings_parts) >= 2:
            setting_type = settings_parts[0].lower()
            setting_value = settings_parts[1]
            
            if setting_type in ['ratio', 'aspect_ratio'] and setting_value in ['16:9', '9:16', '1:1', '4:3']:
                return {'aspect_ratio': setting_value}
            elif setting_type == 'resolution' and setting_value in ['480p', '720p', '1080p']:
                return {'resolution': setting_value}
            elif setting_type == 'fps' and setting_value.isdigit():
                fps_val = int(setting_value)
                if fps_val in [24, 30, 60]:
                    return {'fps': fps_val}
            elif setting_type in ['duration', 'time'] and setting_value.isdigit():
                duration_val = int(setting_value)
                if duration_val in [3, 5, 10]:
                    return {'duration': duration_val}
            break
    
    return updates if updates else None

async def compress_video(video_url: str, max_size_mb: int = 15):
    """Compress video to ensure it's under the specified size limit with high-quality compression (no audio)"""
    input_path = None
    output_path = None
    
    try:
        logger.info(f"Starting high-quality video compression for {video_url}")
        
        # Download the original video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                temp_input.write(chunk)
            
            input_path = temp_input.name
        
        # Create output file
        with tempfile.NamedTemporaryFile(suffix='_compressed.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        # Get detailed video info
        probe = ffmpeg.probe(input_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        duration = float(video_stream['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        fps = eval(video_stream['r_frame_rate'])  # Convert fraction to float
        
        # Enhanced bitrate calculation for better quality
        pixel_count = width * height
        complexity_factor = min(1.2, pixel_count / (1920 * 1080))  # Allow higher bitrate for complex videos
        
        # Smart bitrate allocation - reserve less overhead for better quality
        available_bits = (max_size_mb * 8 * 1024 * 0.95) / duration  # Only 5% overhead
        target_video_bitrate = int(available_bits * complexity_factor)
        
        # Adjust for frame rate more intelligently
        if fps > 30:
            target_video_bitrate = int(target_video_bitrate * 0.85)  # Less aggressive reduction
        elif fps < 24:
            target_video_bitrate = int(target_video_bitrate * 1.1)   # Boost for low fps
        
        logger.info(f"Target video bitrate: {target_video_bitrate}k (optimized for quality)")
        
        # High-quality compression settings (no audio)
        ffmpeg_args = {
            'vcodec': 'libx264',
            'an': None,  # Remove audio completely
            'video_bitrate': f'{target_video_bitrate}k',
            'preset': 'medium',  # Better quality than 'fast'
            'crf': 23,  # Higher quality (lower CRF)
            'profile:v': 'high',  # Better compression efficiency
            'level': '4.0',  # Support higher resolutions
            'movflags': 'faststart',
            'pix_fmt': 'yuv420p',
            'maxrate': f'{int(target_video_bitrate * 1.15)}k',  # Tighter control
            'bufsize': f'{int(target_video_bitrate * 1.8)}k',
            'tune': 'film',  # Optimize for film-like content
            'x264opts': 'ref=3:bframes=3:b-adapt=2:direct=auto:me=umh:subme=8:trellis=1:fast-pskip=0'
        }
        
        # Add smart filtering
        filters = []
        if 'field_order' in video_stream and video_stream['field_order'] != 'progressive':
            filters.append('yadif')  # Deinterlace
        
        # Add noise reduction for better compression
        filters.append('hqdn3d=2:1:2:3')  # Light denoising
        
        if filters:
            ffmpeg_args['vf'] = ','.join(filters)
        
        (
            ffmpeg
            .input(input_path)
            .output(output_path, **ffmpeg_args)
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Check compressed file size
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        logger.info(f"Video compressed: {compressed_size:.2f}MB (target: {max_size_mb}MB)")
        
        # Clean up input file
        os.unlink(input_path)
        
        # If still too large, apply smart secondary compression
        if compressed_size > max_size_mb:
            logger.info("Applying smart secondary compression for size optimization")
            
            with tempfile.NamedTemporaryFile(suffix='_final.mp4', delete=False) as temp_output2:
                output_path2 = temp_output2.name
            
            # Calculate how much we need to reduce
            reduction_factor = max_size_mb / compressed_size
            new_bitrate = int(target_video_bitrate * reduction_factor * 0.9)  # 10% safety margin
            
            # Smart scaling - preserve aspect ratio and quality
            if reduction_factor < 0.7:  # Need significant reduction
                scale_factor = 0.8  # Moderate scaling
            elif reduction_factor < 0.5:  # Need major reduction
                scale_factor = 0.7  # More aggressive scaling
            else:
                scale_factor = 0.9  # Minimal scaling
            
            scale_filter = f'scale=iw*{scale_factor}:ih*{scale_factor}'
            
            # Enhanced secondary compression
            aggressive_args = {
                'vcodec': 'libx264',
                'an': None,
                'video_bitrate': f'{new_bitrate}k',
                'preset': 'slow',  # Better compression efficiency
                'crf': 26,  # Balanced quality
                'profile:v': 'high',
                'vf': f'{scale_filter},hqdn3d=3:2:3:3',  # Scaling + stronger denoising
                'movflags': 'faststart',
                'pix_fmt': 'yuv420p',
                'maxrate': f'{int(new_bitrate * 1.1)}k',
                'bufsize': f'{int(new_bitrate * 1.5)}k',
                'tune': 'film'
            }
            
            (
                ffmpeg
                .input(output_path)
                .output(output_path2, **aggressive_args)
                .overwrite_output()
                .run(quiet=True)
            )
            
            os.unlink(output_path)
            output_path = output_path2
            
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Final optimized size: {final_size:.2f}MB with enhanced quality")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Video compression failed: {e}")
        # Clean up any temp files
        if input_path and os.path.exists(input_path):
            try:
                os.unlink(input_path)
            except:
                pass
        if output_path and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except:
                pass
        
        # Return original URL if compression fails
        return video_url

async def send_whatsapp_message(to: str, message: str, media_url: str = None):
    """Send WhatsApp message - simple and reliable"""
    try:
        message_params = {
            'body': message,
            'from_': 'whatsapp:+14155238886',
            'to': f'whatsapp:{to}'
        }
        
        if media_url:
            message_params['media_url'] = [media_url]
            logger.info(f"📤 Sending with media: {media_url}")
        
        message = twilio_client.messages.create(**message_params)
        logger.info(f"✅ Message sent: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Send failed: {str(e)}")
        return False

async def upload_file_to_temp_server(file_path: str):
    """Upload compressed video to a temporary file server for Twilio access"""
    try:
        # Simple file server endpoint on your backend
        filename = os.path.basename(file_path)
        # Copy file to the /tmp directory that's already mounted as static
        static_path = os.path.join("/tmp", filename)
        import shutil
        shutil.copy2(file_path, static_path)
        
        # Return the public URL where the file can be accessed
        public_url = f"https://peppo-ai-backend-1.onrender.com/static/{filename}"
        logger.info(f"📤 File uploaded to: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return None

async def generate_video_for_whatsapp(phone_number: str, prompt: str):
    """Generate video and send to WhatsApp user"""
    try:
        logger.info(f"Starting video generation for {phone_number}: {prompt}")
        
        # Get user preferences
        prefs = user_preferences.get(phone_number, DEFAULT_SETTINGS)
        
        # Generate video using user preferences (including duration)
        replicate_input = {
            "prompt": prompt,
            "prompt_optimizer": True,
            "aspect_ratio": prefs['aspect_ratio'],
            "fps": prefs['fps']
        }
        
        # Add duration if supported by the model
        if 'duration' in prefs:
            replicate_input['duration'] = prefs['duration']
        
        output = replicate.run(
            "bytedance/seedance-1-pro",
            input=replicate_input
        )
        
        if output:
            # Replicate returns the video URL as a string directly
            video_url = output
        else:
            video_url = None
        
        if video_url:
            logger.info(f"🎬 Generated video URL: {video_url}")
            
            # Use the original video URL directly (no compression needed)
            final_video_url = video_url
            
            # Send success message with video AND URL
            success_msg = (
                f"🎉 **Your video is ready!**\n\n"
                f"📝 Prompt: '{prompt}'\n"
                f"📐 Settings: {prefs['aspect_ratio']}, {prefs['resolution']}, {prefs['fps']}fps, {prefs['duration']}s\n\n"
                f"📹 **Download Link**: {final_video_url}\n\n"
                f"Want another video? Use `{VIDEO_TRIGGER} your new prompt` ✨"
            )
            
            # Send video with URL in message body
            await send_whatsapp_message(phone_number, success_msg, media_url=final_video_url)
            logger.info(f"✅ Video and URL sent successfully")
            
            # Update conversation state
            conversation_state[phone_number] = {
                'stage': 'completed',
                'last_video': final_video_url,
                'completed_at': asyncio.get_event_loop().time()
            }
            
            logger.info(f"Video generated successfully for {phone_number}")
            
        else:
            raise Exception("No video output received")
            
        return {
            "success": True if video_url else False,
            "video_url": video_url
        }
        
    except Exception as e:
        logger.error(f"❌ Video generation failed for {phone_number}: {e}")
        
        # Send error message to user
        error_msg = (
            f"😔 **Oops! Video generation failed**\n\n"
            f"📝 Prompt: '{prompt}'\n"
            f"❌ Error: {str(e)}\n\n"
            f"Please try again with `{VIDEO_TRIGGER} your prompt` 🔄"
        )
        
        await send_whatsapp_message(phone_number, error_msg)
        
        # Update conversation state
        conversation_state[phone_number] = {
            'stage': 'error',
            'error': str(e),
            'failed_at': asyncio.get_event_loop().time()
        }
        
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/generate")
@queued_endpoint
async def generate_video(request: VideoGenerationRequest):
    try:
        output = replicate.run(
            "bytedance/seedance-1-pro",
            input={
                "prompt": request.prompt,
                "prompt_optimizer": True
            }
        )
        return {
            "success": True,
            "video_url": output
        }
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/generate-download")
@queued_endpoint
async def generate_and_download_video(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        output = replicate.run(
            "bytedance/seedance-1-pro",
            input={
                "prompt": prompt,
                "prompt_optimizer": True
            }
        )
        
        if output and len(output) > 0:
            video_url = output
            
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                response = requests.get(video_url)
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            return FileResponse(
                temp_file_path,
                media_type="video/mp4",
                filename=f"generated_video_{hash(prompt)}.mp4"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate video")
            
    except Exception as e:
        logger.error(f"Generate and download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Peppo AI Video Generation API is running!"}

@app.get("/queue-stats")
async def get_queue_stats():
    """Get statistics about the request queue"""
    return request_queue.get_stats()

@app.get("/test-video-url")
async def test_video_url(url: str):
    """Test endpoint to validate video URLs"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        return {
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type'),
            "content_length": response.headers.get('content-length'),
            "size_mb": round(int(response.headers.get('content-length', 0)) / (1024 * 1024), 2) if response.headers.get('content-length') else None,
            "headers": dict(response.headers),
            "accessible": response.status_code == 200,
            "is_video": response.headers.get('content-type', '').startswith('video/')
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "accessible": False
        }

# Add trigger configuration
VIDEO_TRIGGER = "!generate"  # Users type "!generate your prompt here"

async def handle_incoming_message(phone_number: str, message_body: str):
    """Handle all incoming WhatsApp messages with proper routing"""
    try:
        logger.info(f"📱 Incoming message from {phone_number}: {message_body}")
        
        # Handle settings commands
        if message_body.startswith('/settings'):
            return await handle_settings_command(phone_number, message_body)
        
        # Handle help command
        elif message_body.startswith('/help'):
            help_msg = (
                "🤖 **Video Generator Bot Help**\n\n"
                f"🎬 **Generate Video**: `{VIDEO_TRIGGER} your prompt here`\n"
                "⚙️ **Settings**: `/settings` or `/settings aspect_ratio=1:1`\n"
                "❓ **Help**: `/help`\n\n"
                "**Available Settings:**\n"
                "• `aspect_ratio`: 16:9, 1:1, 9:16\n"
                "• `resolution`: 720p, 1080p, 480p\n"
                "• `fps`: 24, 30, 60\n"
                "• `duration`: 3, 5, 10 (seconds)\n\n"
                f"**Example**: `{VIDEO_TRIGGER} a cat playing with a ball`"
            )
            await send_whatsapp_message(phone_number, help_msg)
            return True
        
        # Handle video generation trigger
        elif message_body.startswith(VIDEO_TRIGGER):
            prompt = message_body[len(VIDEO_TRIGGER):].strip()
            if not prompt:
                await send_whatsapp_message(phone_number, 
                    f"❌ Please provide a prompt after {VIDEO_TRIGGER}\n\n"
                    f"Example: `{VIDEO_TRIGGER} a sunset over the ocean`")
                return True
            
            return await handle_video_generation(phone_number, prompt)
        
        # Handle regular messages (no trigger)
        else:
            welcome_msg = (
                f"👋 Hi! I'm your video generator bot.\n\n"
                f"🎬 To generate a video, use: `{VIDEO_TRIGGER} your prompt`\n"
                f"⚙️ To change settings, use: `/settings`\n"
                f"❓ For help, use: `/help`\n\n"
                f"**Example**: `{VIDEO_TRIGGER} a dog running in a park`"
            )
            await send_whatsapp_message(phone_number, welcome_msg)
            return True
            
    except Exception as e:
        logger.error(f"❌ Error handling message from {phone_number}: {e}")
        await send_whatsapp_message(phone_number, 
            "❌ Sorry, something went wrong. Please try again or use `/help` for assistance.")
        return False

async def handle_video_generation(phone_number: str, prompt: str):
    """Handle video generation requests with proper error handling"""
    try:
        logger.info(f"🎬 Starting video generation for {phone_number}: {prompt}")
        
        # Update conversation state
        conversation_state[phone_number] = {
            'stage': 'generating',
            'prompt': prompt,
            'started_at': asyncio.get_event_loop().time()
        }
        
        # Send acknowledgment
        ack_msg = (
            f"🎬 **Generating your video...**\n\n"
            f"📝 Prompt: '{prompt}'\n"
            f"⏱️ This usually takes 30-60 seconds\n\n"
            f"Please wait... ⏳"
        )
        await send_whatsapp_message(phone_number, ack_msg)
        
        # Content moderation
        if not await moderate_content(prompt):
            await send_whatsapp_message(phone_number, 
                "❌ **Content Moderation Alert**\n\n"
                "Your prompt contains inappropriate content. Please try a different prompt.")
            conversation_state[phone_number] = {'stage': 'rejected'}
            return False
        
        # Get user preferences
        prefs = user_preferences.get(phone_number, DEFAULT_SETTINGS)
        logger.info(f"📐 Using settings: {prefs}")
        
        # Send a funny waiting message after a short delay
        await asyncio.sleep(5)  # Wait 5 seconds before sending the funny message
        funny_msg = (
            f"🎭 **Your video is in the queue!**\n\n"
            f"🧙‍♂️ Our AI wizards are hard at work creating your masterpiece...\n"
            f"🎬 Prompt: '{prompt}'\n\n"
            f"🔄 Position in queue: {request_queue.queue.qsize() + 1}\n"
            f"⏳ Estimated time remaining: {random.randint(10, 30)} seconds\n\n"
            f"Did you know? Each video is uniquely crafted just for you! 🌟"
        )
        await send_whatsapp_message(phone_number, funny_msg)
        
        # Generate video using Replicate - bytedance/seedance-1-pro supports all parameters
        replicate_input = {
            "prompt": prompt,
            "duration": prefs['duration'],
            "resolution": prefs['resolution'], 
            "aspect_ratio": prefs['aspect_ratio'],
            "fps": prefs['fps'],
            "camera_fixed": False
        }
        
        logger.info(f"🔄 Calling Replicate with: {replicate_input}")
        output = replicate.run("bytedance/seedance-1-pro", input=replicate_input)
        
        if output and len(output) > 0:
            video_url = output
            logger.info(f"✅ Video generated: {video_url}")
            
            # Handle the generated video
            return await handle_generated_video(phone_number, prompt, video_url, prefs)
        else:
            raise Exception("No video output received from Replicate")
            
    except Exception as e:
        logger.error(f"❌ Video generation failed for {phone_number}: {e}")
        
        error_msg = (
            f"❌ **Video Generation Failed**\n\n"
            f"📝 Prompt: '{prompt}'\n"
            f"🔧 Error: {str(e)}\n\n"
            f"Please try again with a different prompt or use `/help` for assistance."
        )
        await send_whatsapp_message(phone_number, error_msg)
        
        conversation_state[phone_number] = {
            'stage': 'failed',
            'error': str(e)
        }
        return False

async def handle_generated_video(phone_number: str, prompt: str, video_url: str, prefs: dict):
    """Handle the video received from Replicate - compress and send"""
    try:
        logger.info(f"📹 Processing generated video: {video_url}")
        
        # Optional validation (non-blocking)
        try:
            response = requests.head(video_url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', 'unknown')
                logger.info(f"✅ Video accessible: {content_type}, {content_length} bytes")
            else:
                logger.warning(f"⚠️ Video URL returned {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not validate video URL: {e}")
        
        # Compress video if needed
        compressed_video_path = await compress_video(video_url, max_size_mb=15)
        
        # Determine final video URL
        final_video_url = video_url  # Default to original
        
        if compressed_video_path and compressed_video_path != video_url:
            # Try to upload compressed video
            uploaded_url = await upload_file_to_temp_server(compressed_video_path)
            if uploaded_url:
                final_video_url = uploaded_url
                logger.info(f"📤 Using uploaded compressed video: {uploaded_url}")
            else:
                logger.warning(f"⚠️ Upload failed, using original URL")
            
            # Clean up local file
            try:
                if os.path.exists(compressed_video_path):
                    os.unlink(compressed_video_path)
            except:
                pass
        
        logger.info(f"🎯 Final video URL for delivery: {final_video_url}")
        
        # Send success message with video
        success_msg = (
            f"🎉 **Your video is ready!**\n\n"
            f"📝 Prompt: '{prompt}'\n"
            f"📐 Settings: {prefs['aspect_ratio']}, {prefs['resolution']}, {prefs['fps']}fps, {prefs['duration']}s\n\n"
            f"Want another video? Use `{VIDEO_TRIGGER} your new prompt` ✨"
        )
        
        # Try to send video as media attachment
        logger.info(f"🚀 Attempting to send video as media attachment...")
        video_sent = await send_whatsapp_message(phone_number, success_msg, media_url=final_video_url)
        
        if not video_sent:
            # Fallback: send URL if video delivery fails
            logger.info(f"📋 Media delivery failed, sending fallback URL message...")
            fallback_msg = (
                f"🎉 **Video Generated Successfully!**\n\n"
                f"📝 Prompt: '{prompt}'\n"
                f"📐 Settings: {prefs['aspect_ratio']}, {prefs['resolution']}, {prefs['fps']}fps, {prefs['duration']}s\n\n"
                f"📹 **Video URL**: {final_video_url}\n\n"
                f"⚠️ Video couldn't be delivered directly. Click the URL above to download.\n\n"
                f"Want another video? Use `{VIDEO_TRIGGER} your new prompt` ✨"
            )
            fallback_sent = await send_whatsapp_message(phone_number, fallback_msg)
            if fallback_sent:
                logger.info(f"✅ Fallback URL message sent successfully")
            else:
                logger.error(f"❌ Both media and fallback message failed!")
        else:
            logger.info(f"✅ Video delivered successfully as media attachment")
        
        # Update conversation state
        conversation_state[phone_number] = {
            'stage': 'completed',
            'last_video': final_video_url,
            'completed_at': asyncio.get_event_loop().time()
        }
        
        logger.info(f"✅ Video successfully delivered to {phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to handle generated video: {e}")
        
        error_msg = (
            f"❌ **Video Processing Failed**\n\n"
            f"📝 Prompt: '{prompt}'\n"
            f"🔧 Error: {str(e)}\n\n"
            f"The video was generated but couldn't be processed. Please try again."
        )
        await send_whatsapp_message(phone_number, error_msg)
        return False

async def handle_settings_command(phone_number: str, message_body: str):
    """Handle settings commands separately"""
    try:
        if message_body.strip() == '/settings':
            # Show current settings
            prefs = user_preferences.get(phone_number, DEFAULT_SETTINGS)
            settings_msg = (
                f"⚙️ **Current Settings**\n\n"
                f"📐 Aspect Ratio: `{prefs['aspect_ratio']}`\n"
                f"📺 Resolution: `{prefs['resolution']}`\n"
                f"🎞️ FPS: `{prefs['fps']}`\n"
                f"⏱️ Duration: `{prefs['duration']}s`\n\n"
                f"**To change settings:**\n"
                f"`/settings aspect_ratio=1:1`\n"
                f"`/settings resolution=1080p fps=60`\n"
                f"`/settings duration=10`"
            )
            await send_whatsapp_message(phone_number, settings_msg)
            return True
        else:
            # Parse and update settings
            updates = parse_settings_command(message_body)
            if updates:
                if phone_number not in user_preferences:
                    user_preferences[phone_number] = DEFAULT_SETTINGS.copy()
                
                user_preferences[phone_number].update(updates)
                prefs = user_preferences[phone_number]
                
                success_msg = (
                    f"✅ **Settings Updated**\n\n"
                    f"📐 Aspect Ratio: `{prefs['aspect_ratio']}`\n"
                    f"📺 Resolution: `{prefs['resolution']}`\n"
                    f"🎞️ FPS: `{prefs['fps']}`\n"
                    f"⏱️ Duration: `{prefs['duration']}s`\n\n"
                    f"Ready for video generation! Use `{VIDEO_TRIGGER} your prompt`"
                )
                await send_whatsapp_message(phone_number, success_msg)
                return True
            else:
                await send_whatsapp_message(phone_number, 
                    "❌ Invalid settings format. Use `/settings` to see current settings.")
                return False
                
    except Exception as e:
        logger.error(f"❌ Settings command failed: {e}")
        await send_whatsapp_message(phone_number, 
            "❌ Settings update failed. Please try again.")
        return False

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """Enhanced Twilio webhook for WhatsApp messages - returns proper TwiML"""
    try:
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '').strip()
        
        logger.info(f"📨 Webhook received from {from_number}: {message_body}")
        
        # Create TwiML response
        resp = MessagingResponse()
        
        if not from_number or not message_body:
            logger.warning("❌ Invalid webhook data received")
            # Return empty TwiML response
            return Response(content=str(resp), media_type="application/xml")
        
        # Queue the message handling instead of creating a task directly
        await request_queue.add_task(handle_incoming_message, from_number, message_body)
        
        # Return empty TwiML response immediately (Twilio requirement)
        return Response(content=str(resp), media_type="application/xml")
            
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        # Always return valid TwiML even on error
        resp = MessagingResponse()
        return Response(content=str(resp), media_type="application/xml")

from fastapi.staticfiles import StaticFiles

# Add this after your app initialization
app.mount("/static", StaticFiles(directory="/tmp"), name="static")