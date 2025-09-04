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
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import asyncio
import logging
import urllib.request
from urllib.parse import urlparse
import ffmpeg

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
    'aspect_ratio': '16:9',
    'resolution': '720p',
    'fps': 30,
    'duration': 5
}

# Pydantic models
class VideoGenerationRequest(BaseModel):
    prompt: str
    fps: Optional[int] = 24
    duration: Optional[int] = 5
    resolution: Optional[str] = "480"
    aspect_ratio: Optional[str] = "16:9"

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
    """Parse settings commands like '/settings ratio 16:9'"""
    parts = message.lower().split()
    if len(parts) < 3:
        return None
    
    setting_type = parts[1]
    setting_value = parts[2]
    
    if setting_type == 'ratio' and setting_value in ['16:9', '9:16', '1:1', '4:3']:
        return {'aspect_ratio': setting_value}
    elif setting_type == 'resolution' and setting_value in ['480p', '720p', '1080p']:
        return {'resolution': setting_value}
    elif setting_type == 'fps' and setting_value.isdigit():
        fps_val = int(setting_value)
        if fps_val in [24, 30, 60]:
            return {'fps': fps_val}
    elif setting_type == 'duration' and setting_value.isdigit():
        duration_val = int(setting_value)
        if duration_val in [3, 5, 10]:
            return {'duration': duration_val}
    
    return None

# Simplified video compression (placeholder - no actual compression for now)
async def compress_video(video_url: str, max_size_mb: int = 15):
    """Compress video to ensure it's under the specified size limit"""
    try:
        logger.info(f"Starting video compression for {video_url}")
        
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
        
        # Get video info
        probe = ffmpeg.probe(input_path)
        duration = float(probe['streams'][0]['duration'])
        
        # Calculate target bitrate (in kbps) to stay under max_size_mb
        # Formula: (target_size_mb * 8 * 1024) / duration_seconds
        target_bitrate = int((max_size_mb * 8 * 1024) / duration * 0.9)  # 90% to leave some margin
        
        # Compress video with ffmpeg
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vcodec='libx264',
                acodec='aac',
                video_bitrate=f'{target_bitrate}k',
                audio_bitrate='128k',
                preset='medium',
                crf=28,
                movflags='faststart'
            )
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Check compressed file size
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        logger.info(f"Video compressed: {compressed_size:.2f}MB (target: {max_size_mb}MB)")
        
        # Clean up input file
        os.unlink(input_path)
        
        # If still too large, try more aggressive compression
        if compressed_size > max_size_mb:
            logger.info("File still too large, applying more aggressive compression")
            
            with tempfile.NamedTemporaryFile(suffix='_compressed2.mp4', delete=False) as temp_output2:
                output_path2 = temp_output2.name
            
            # More aggressive settings
            target_bitrate = int(target_bitrate * 0.7)  # Reduce bitrate by 30%
            
            (
                ffmpeg
                .input(output_path)
                .output(
                    output_path2,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate=f'{target_bitrate}k',
                    audio_bitrate='96k',
                    preset='medium',
                    crf=32,
                    vf='scale=iw*0.8:ih*0.8',  # Reduce resolution by 20%
                    movflags='faststart'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            os.unlink(output_path)
            output_path = output_path2
            
            final_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Final compressed size: {final_size:.2f}MB")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Video compression failed: {e}")
        # Clean up any temp files
        for path in [input_path, output_path]:
            try:
                if 'path' in locals() and os.path.exists(path):
                    os.unlink(path)
            except:
                pass
        
        # Return original URL if compression fails
        return video_url

async def send_whatsapp_message(to: str, message: str, media_url: str = None):
    """Send WhatsApp message via Twilio (enhanced with media support)"""
    try:
        message_params = {
            'body': message,
            'from_': 'whatsapp:+14155238886',  # Twilio sandbox number
            'to': f'whatsapp:{to}'
        }
        
        if media_url:
            message_params['media_url'] = [media_url]
        
        message = twilio_client.messages.create(**message_params)
        logger.info(f"Message sent to {to}: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to}: {e}")
        return False

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from Twilio (enhanced)"""
    try:
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '').strip()
        
        logger.info(f"Received message from {from_number}: {message_body}")
        
        # Initialize user state if not exists
        if from_number not in conversation_state:
            conversation_state[from_number] = {'stage': 'initial'}
        if from_number not in user_preferences:
            user_preferences[from_number] = DEFAULT_SETTINGS.copy()
        
        current_state = conversation_state[from_number]
        
        # Handle settings commands
        if message_body.lower().startswith('/settings'):
            if message_body.lower() == '/settings':
                prefs = user_preferences[from_number]
                settings_msg = ("⚙️ **Your Current Video Settings:**\n\n"
                              f"📐 Aspect Ratio: {prefs['aspect_ratio']}\n"
                              f"🎥 Resolution: {prefs['resolution']}\n"
                              f"⚡ FPS: {prefs['fps']}\n"
                              f"⏱️ Duration: {prefs['duration']} seconds\n\n"
                              "**To change settings, use:**\n"
                              "• `/settings ratio 16:9` (16:9, 9:16, 1:1, 4:3)\n"
                              "• `/settings resolution 720p` (480p, 720p, 1080p)\n"
                              "• `/settings fps 30` (24, 30, 60)\n"
                              "• `/settings duration 10` (3, 5, 10)")
                await send_whatsapp_message(from_number, settings_msg)
            else:
                new_setting = parse_settings_command(message_body)
                if new_setting:
                    user_preferences[from_number].update(new_setting)
                    setting_name = list(new_setting.keys())[0]
                    setting_value = new_setting[setting_name]
                    await send_whatsapp_message(from_number, f"✅ Updated {setting_name} to {setting_value}")
                else:
                    await send_whatsapp_message(from_number, "❌ Invalid setting. Use `/settings` to see available options.")
            
            return MessagingResponse()
        
        # Handle help command
        if message_body.lower() in ['/help', 'help']:
            help_msg = ("🤖 **Peppo AI Video Bot Help**\n\n"
                       "**Commands:**\n"
                       "• Send any text to generate a video\n"
                       "• `/settings` - View/change video settings\n"
                       "• `/help` - Show this help message\n\n"
                       "**Video Settings:**\n"
                       "• Aspect ratios: 16:9, 9:16, 1:1, 4:3\n"
                       "• Resolutions: 480p, 720p, 1080p\n"
                       "• FPS: 24, 30, 60\n"
                       "• Duration: 3, 5, 10 seconds\n\n"
                       "Just send me a description and I'll create a video for you! 🎬")
            await send_whatsapp_message(from_number, help_msg)
            return MessagingResponse()
        
        # Check if user is in video generation process
        if current_state.get('stage') == 'generating':
            await send_whatsapp_message(from_number, "🎬 I'm still working on your previous video! Please wait a moment...")
            return MessagingResponse()
        
        # Handle regular messages (video generation requests)
        if len(message_body) < 10:
            await send_whatsapp_message(from_number, 
                "📝 Please provide a more detailed description (at least 10 characters) for better video generation!\n\n"
                "Example: 'A cat playing with a ball in a sunny garden'")
            return MessagingResponse()
        
        # Content moderation
        is_appropriate, moderation_msg = await moderate_content(message_body)
        if not is_appropriate:
            await send_whatsapp_message(from_number, 
                f"🚫 Sorry, I can't generate a video for that content.\n\n"
                f"Reason: {moderation_msg}\n\n"
                "Please try with a different, appropriate description.")
            return MessagingResponse()
        
        # Start video generation
        conversation_state[from_number] = {'stage': 'generating'}
        
        # Send acknowledgment
        prefs = user_preferences[from_number]
        ack_msg = (f"🎬 **Creating your video!**\n\n"
                  f"📝 Prompt: '{message_body}'\n"
                  f"📐 Ratio: {prefs['aspect_ratio']}\n"
                  f"🎥 Resolution: {prefs['resolution']}\n\n"
                  "⏳ This usually takes 1-2 minutes. I'll send it to you when ready!")
        
        await send_whatsapp_message(from_number, ack_msg)
        
        # Start video generation in background
        asyncio.create_task(generate_video_for_whatsapp(from_number, message_body))
        
        return MessagingResponse()
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return MessagingResponse()

async def generate_video_for_whatsapp(phone_number: str, prompt: str):
    """Generate video and send to WhatsApp user"""
    try:
        logger.info(f"Starting video generation for {phone_number}: {prompt}")
        
        # Get user preferences
        prefs = user_preferences.get(phone_number, DEFAULT_SETTINGS)
        
        # Generate video using user preferences
        output = replicate.run(
            "minimax/video-01",
            input={
                "prompt": prompt,
                "prompt_optimizer": True,
                "aspect_ratio": prefs['aspect_ratio'],
                "fps": prefs['fps']
            }
        )
        
        if output and len(output) > 0:
            video_url = output[0]
            
            # Compress video to ensure it's under 16MB (placeholder for now)
            compressed_video_path = await compress_video(video_url, max_size_mb=15)
            
            # Send success message with video
            success_msg = ("🎉 **Your video is ready!**\n\n"
                          f"📝 Prompt: '{prompt}'\n"
                          f"📐 Settings: {prefs['aspect_ratio']}, {prefs['resolution']}, {prefs['fps']}fps\n\n"
                          "Want to create another video? Just send me a new prompt! ✨")
            
            await send_whatsapp_message(phone_number, success_msg, media_url=video_url)
            
            # Update conversation state
            conversation_state[phone_number] = {
                'stage': 'completed',
                'last_video': video_url
            }
            
            logger.info(f"Video generated successfully for {phone_number}")
            
        else:
            raise Exception("No video output received")
            
    except Exception as e:
        logger.error(f"Video generation failed for {phone_number}: {e}")
        
        # Send error message
        error_msg = ("😔 Sorry, I couldn't generate your video right now.\n\n"
                    "This could be due to:\n"
                    "• High server load\n"
                    "• Complex prompt requirements\n"
                    "• Temporary service issues\n\n"
                    "Please try again with a simpler prompt, or wait a few minutes and retry! 🔄")
        
        await send_whatsapp_message(phone_number, error_msg)
        
        # Reset conversation state
        conversation_state[phone_number] = {'stage': 'initial'}

@app.post("/generate")
async def generate_video(request: VideoGenerationRequest):
    try:
        output = replicate.run(
            "minimax/video-01",
            input={
                "prompt": request.prompt,
                "prompt_optimizer": True
            }
        )
        return {
            "success": True,
            "video_url": output[0] if output else None
        }
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/generate-download")
async def generate_and_download_video(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        output = replicate.run(
            "minimax/video-01",
            input={
                "prompt": prompt,
                "prompt_optimizer": True
            }
        )
        
        if output and len(output) > 0:
            video_url = output[0]
            
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
