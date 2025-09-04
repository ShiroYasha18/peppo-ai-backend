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

# Load .env from current directory (not parent directory)
load_dotenv()

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

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for request validation
class VideoGenerationRequest(BaseModel):
    api_key: Optional[str] = None
    prompt: str
    fps: Optional[int] = 24
    duration: Optional[int] = 5
    resolution: Optional[str] = "720p"
    aspect_ratio: Optional[str] = "16:9"
    camera_fixed: Optional[bool] = False

# Store for tracking conversation state (in production, use Redis or database)
conversation_state = {}

async def send_whatsapp_message(to: str, message: str):
    """Send a WhatsApp message via Twilio"""
    try:
        # Ensure the phone number format is correct
        if not to.startswith('+'):
            to = f'+{to}'
            
        message_obj = twilio_client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',  # Twilio sandbox number
            to=f'whatsapp:{to}'
        )
        logger.info(f"Message sent successfully to {to}: {message_obj.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to}: {str(e)}")
        return False

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        form_data = await request.form()
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '').strip()
        
        logger.info(f"Received message from {from_number}: {message_body}")
        
        # Create TwiML response
        resp = MessagingResponse()
        
        # Handle different conversation states
        user_state = conversation_state.get(from_number, {'stage': 'initial'})
        
        if message_body.lower() in ['hi', 'hello', 'start', 'help']:
            # Welcome message
            welcome_msg = ("🎬 Welcome to AI Video Generator!\n\n"
                         "Send me a text prompt and I'll create a video for you.\n\n"
                         "Example: 'A cat playing piano in a cozy room'\n\n"
                         "Type your prompt to get started! ✨")
            resp.message(welcome_msg)
            conversation_state[from_number] = {'stage': 'waiting_for_prompt'}
            
            # Also send via Twilio API (backup method)
            await send_whatsapp_message(from_number, welcome_msg)
            
        elif len(message_body) < 10:
            # Prompt too short
            error_msg = ("🤔 That prompt is too short!\n\n"
                        "Try something more descriptive like:\n"
                        "• 'A golden retriever running through a field of sunflowers'\n"
                        "• 'Waves crashing on a rocky coastline at sunset'\n"
                        "• 'A steaming cup of coffee on a wooden table'\n\n"
                        "Please send a longer, more detailed prompt! 📝")
            resp.message(error_msg)
            
            # Also send via Twilio API (backup method)
            await send_whatsapp_message(from_number, error_msg)
            
        else:
            # Process video generation request
            ack_msg = ("🎬 Got it! Generating your video...\n\n"
                      f"Prompt: '{message_body}'\n\n"
                      "This usually takes 2-3 minutes. I'll send you the video when it's ready! ⏳")
            resp.message(ack_msg)
            
            # Also send via Twilio API (backup method)
            await send_whatsapp_message(from_number, ack_msg)
            
            # Update conversation state
            conversation_state[from_number] = {
                'stage': 'generating',
                'prompt': message_body
            }
            
            # Start video generation in background
            asyncio.create_task(generate_video_for_whatsapp(from_number, message_body))
                
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        resp = MessagingResponse()
        error_msg = ("😅 Oops! Something went wrong on my end.\n\n"
                    "Please try again in a moment, or contact support if the issue persists.")
        resp.message(error_msg)
    
    return str(resp)

async def generate_video_for_whatsapp(phone_number: str, prompt: str):
    """Generate video and send to WhatsApp user"""
    try:
        logger.info(f"Starting video generation for {phone_number}: {prompt}")
        
        # Generate video using existing logic
        output = replicate.run(
            "minimax/video-01",
            input={
                "prompt": prompt,
                "prompt_optimizer": True
            }
        )
        
        if output and len(output) > 0:
            video_url = output[0]
            
            # Send success message with video
            success_msg = ("🎉 Your video is ready!\n\n"
                          f"Prompt: '{prompt}'\n\n"
                          f"Watch it here: {video_url}\n\n"
                          "Want to create another video? Just send me a new prompt! ✨")
            
            await send_whatsapp_message(phone_number, success_msg)
            
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
        
        if output and len(output) > 0:
            return {
                "success": True,
                "video_url": output[0],
                "prompt": request.prompt
            }
        else:
            raise HTTPException(status_code=500, detail="Video generation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating video: {str(e)}")

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
            
            response = requests.get(video_url)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                return FileResponse(
                    temp_file_path,
                    media_type="video/mp4",
                    filename=f"generated_video_{hash(prompt)}.mp4"
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to download video")
        else:
            raise HTTPException(status_code=500, detail="Video generation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI Video Generator API is running!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
