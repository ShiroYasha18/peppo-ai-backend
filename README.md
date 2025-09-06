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


PlainText



## Usage### Starting the Server```bashcd backenduvicorn main:app --reload --host 0.0.0.0 --port 8000```### WhatsApp Commands- **Generate Video**: Send any text prompt to generate a video- **/settings**: Configure video parameters  - Example: `/settings ratio=16:9   resolution=720p fps=24 duration=5`## API Endpoints### POST /whatsapp/webhookReceives incoming WhatsApp messages via Twilio.**Request Body:**
Form data with WhatsApp message content

PlainText



**Response:**TwiML response for Twilio### GET /Health check endpoint.**Response:**```json{  "message": "WhatsApp Video Generation   API is running!"}```### GET /queue/statsGet current queue statistics.**Response:**```json{  "queue_size": "integer",  "active_tasks": "integer"}```## DeploymentThe project is configured for deployment on Render.com:```yamlservices:  - type: web    name: peppo-ai-backend    env: python    buildCommand: "cd backend && pip     install -r requirements.txt"    startCommand: "cd backend && uvicorn     main:app --host 0.0.0.0 --port $PORT"    envVars:      - key: REPLICATE_API_TOKEN        sync: false      - key: TWILIO_ACCOUNT_SID        sync: false      - key: TWILIO_AUTH_TOKEN        sync: false      - key: TWILIO_PHONE_NUMBER        sync: false      - key: OPENAI_API_KEY        sync: false      - key: TEMP_SERVER_URL        sync: false```## Troubleshooting### Common Issues & Solutions#### 🔴 "REPLICATE_API_TOKEN not found"**Solution:**Check your .env file exists and has the correct token in the backend directory.#### 🔴 WhatsApp Message Delivery Fails**Solutions:**- Verify your Twilio credentials are correct- Ensure the temporary server URL is accessible from the internet- Check that video files are properly compressed to under 16MB#### 🔴 Video Generation Fails**Solutions:**- Verify your Replicate API token has sufficient credits- Check that the prompt meets minimum requirements- Try simpler prompts if complex ones fail## LicenseThis project is licensed under the MIT License.## Author**Ayraf** - *Full Stack Developer*- GitHub: [@ayrafraihan](https://github.com/ayrafraihan)- Made with ❤️ and lots of ☕

