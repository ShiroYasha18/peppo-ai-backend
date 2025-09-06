# Peppo WhatsApp Video Generation Bot 🎬✨

> Transform your WhatsApp messages into stunning AI-generated videos with simple text prompts!

## Overview

Peppo is a WhatsApp bot that leverages AI to generate videos from text prompts. Send a message to the bot, and it will create a video based on your description using the ByteDance SeedANCE model via Replicate.

## Features

🎥 **AI Video Generation** - Transform text prompts into stunning videos using ByteDance SeedANCE model  
🤖 **WhatsApp Integration** - Seamless interaction through WhatsApp messaging  
⚙️ **Customizable Parameters** - Control video settings with simple commands  
🔍 **Content Moderation** - OpenAI-powered content filtering for safe usage  
⚡ **Queue Management** - Efficient handling of multiple video generation requests  
🎬 **Video Compression** - Automatic compression to ensure WhatsApp compatibility  

## Tech Stack

- **FastAPI** - High-performance Python web framework
- **Twilio** - WhatsApp messaging integration
- **Replicate** - AI model hosting and inference
- **OpenAI** - Content moderation
- **FFmpeg** - Video compression
- **Uvicorn** - ASGI server for production
- **Pydantic** - Data validation and serialization
- **Python-dotenv** - Environment variable management

## Setup

### Prerequisites

- Python 3.8+
- Twilio account with WhatsApp integration
- Replicate API token
- OpenAI API key
- FFmpeg installed on your system

### Installation

```bash
# Clone the repository
git clone <>
cd peppo

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the backend directory with the following variables:
REPLICATE_API_TOKEN=your_replicate_token 
TWILIO_ACCOUNT_SID=your_twilio_sid 
TWILIO_AUTH_TOKEN=your_twilio_token 
TWILIO_PHONE_NUMBER=whatsapp:+14155238886  # default number 






## Usage

### Starting the Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### WhatsApp Commands

- **Generate Video**: Send any text prompt to generate a video
- **/settings**: Configure video parameters  
  - Example: `/settings ratio=16:9   resolution=720p fps=24 duration=5`

## API Endpoints
### POST /webhook
This endpoint receives incoming WhatsApp messages via Twilio's webhook system.

Request:

- Receives form data from Twilio containing WhatsApp message details
- Key parameters:
  - From : The sender's WhatsApp number (format: whatsapp:+1234567890 )
  - Body : The text content of the message
Processing:

- Extracts the phone number and message content
- Queues the message for processing using the request queue system
- Handles various message types:
  - Text prompts prefixed with !generate to create videos
  - Settings commands starting with /settings
  - Help requests with /help
  - Regular messages (responds with welcome instructions)
Response:

- Returns a TwiML (Twilio Markup Language) response
- Content-Type: application/xml
- This response is required by Twilio to acknowledge receipt of the webhook

 Made with ❤️ and lots of ☕

