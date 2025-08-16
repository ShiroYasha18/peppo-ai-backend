# Peppo AI 🎬✨

> Transform your ideas into stunning videos with AI magic! Simple, fast, and incredibly fun to use.

## Demo

![Peppo AI Demo](./demovid.mov)

*Watch the demo video to see Peppo AI in action!*

## Overview

Peppo AI is a modern full-stack web application that leverages Replicate's AI models to generate videos from text prompts. Built with a sleek orange and black design, it provides an intuitive interface for creating AI-powered videos with customizable parameters using the ByteDance SeedANCE-1-Lite model.

## Features

🎥 **AI Video Generation** - Transform text prompts into stunning videos using ByteDance SeedANCE-1-Lite
🎨 **Modern UI** - Beautiful orange and black themed interface with glass morphism effects
⚙️ **Customizable Parameters** - Control FPS (24), duration (1-10s), resolution (720p/1080p), aspect ratio (16:9/9:16/1:1), and camera settings
🔐 **Secure API Key Management** - Safe storage and validation of Replicate API credentials
📱 **Responsive Design** - Works seamlessly on desktop and mobile devices
⚡ **Real-time Progress** - Live updates during video generation
💾 **Easy Download** - Direct video download functionality
🌐 **CORS Enabled** - Full cross-origin support for frontend-backend communication

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling with custom orange/black theme
- **Lucide React** - Beautiful icons
- **React Hooks** - Modern state management

### Backend
- **FastAPI** - High-performance Python web framework
- **Replicate** - AI model hosting and inference
- **Uvicorn** - ASGI server for production
- **Pydantic** - Data validation and serialization
- **Python-dotenv** - Environment variable management

### AI Model
- **ByteDance SeedANCE-1-Lite** - Advanced video generation model via Replicate

## Project Structure
peppo/ ├── frontend/ # Next.js frontend application │ ├── src/ │ │ ├── app/ # App Router pages │ │ │ ├── page.tsx # Main application page │ │ │ ├── layout.tsx # Root layout │ │ │ └── api/ # API routes │ │ ├── components/ # Reusable UI components │ │ │ ├── ApiKeyInput.tsx │ │ │ ├── PromptInput.tsx │ │ │ ├── ParameterSliders.tsx │ │ │ ├── VideoGenerator.tsx │ │ │ └── ClientWrapper.tsx │ │ ├── contexts/ # React contexts │ │ │ └── ThemeContext.tsx │ │ ├── lib/ # Utility functions │ │ └── types/ # TypeScript type definitions │ ├── package.json │ └── tsconfig.json ├── backend/ # FastAPI backend │ ├── main.py # Main application file │ ├── requirements.txt # Python dependencies │ └── .env # Environment variables (not in repo) ├── demovid.mov # Demo video ├── render.yaml # Render deployment config └── README.md # This file

PlainText



## API Endpoints### POST /generateGenerate a video from a text prompt with custom parameters.**Request Body:**```json{  "api_key": "string (optional)",  "prompt": "string (required, min 3   chars)",  "fps": "integer (optional, default: 24)  ",  "duration": "integer (optional,   default: 5, max: 10)",  "resolution": "string (optional,   default: '720p', options: '720p'|  '1080p')",  "aspect_ratio": "string (optional,   default: '16:9', options: '16:9'|'9:16'|  '1:1')",  "camera_fixed": "boolean (optional,   default: false)"}```**Response:**```json{  "video_url": "string",  "message": "Video generated   successfully",  "prompt_used": "string",  "duration": "string",  "resolution": "string",  "fps": "integer",  "aspect_ratio": "string",  "camera_fixed": "boolean"}```### POST /generate-downloadGenerate and directly download a video file.**Request Body:**```json{  "prompt": "string (required, min 3   chars)"}```**Response:** Direct MP4 file download### GET /Health check endpoint.**Response:**```json{  "message": "Video Generation API is   running!"}```## Getting Started### Prerequisites- Node.js 18+ and npm- Python 3.8+- Replicate API token (get one at [replicate.com](https://replicate.com))### Environment Setup1. Create a `.env` file in the backend directory:   ```bash   cd backend   touch .env   ```2. Add your Replicate API token:   ```env   REPLICATE_API_TOKEN=your_replicate_toke   n_here   ```### Frontend Setup1. Navigate to the frontend directory:   ```bash   cd frontend   ```2. Install dependencies:   ```bash   npm install   ```3. Start the development server:   ```bash   npm run dev   ```4. Open [http://localhost:3000](http://localhost:3000) in your browser### Backend Setup1. Navigate to the backend directory:   ```bash   cd backend   ```2. Install Python dependencies:   ```bash   pip install -r requirements.txt   ```3. Start the FastAPI server:   ```bash   uvicorn main:app --reload --port 8000   ```4. The API will be available at [http://localhost:8000](http://localhost:8000)## Usage1. **Enter API Key**: Input your Replicate API key in the secure field (optional if set in backend .env)2. **Write Your Prompt**: Describe the video you want to create (minimum 3 characters)3. **Adjust Parameters**:    - **FPS**: Frame rate (default: 24)   - **Duration**: Video length in    seconds (1-10, default: 5)   - **Resolution**: Video quality (720p/   1080p, default: 720p)   - **Aspect Ratio**: Video dimensions    (16:9/9:16/1:1, default: 16:9)   - **Camera Fixed**: Whether camera    should be stationary (default: false)4. **Generate Video**: Click the generate button and watch the magic happen5. **Download**: Save your generated video to your device## Components### Core Components- **ApiKeyInput** - Secure API key management with validation and visibility toggle- **PromptInput** - Text area for video prompts with character counting and validation- **ParameterSliders** - Interactive controls for FPS, duration, resolution, aspect ratio, and camera settings- **VideoGenerator** - Main generation interface with progress tracking and video preview- **ClientWrapper** - Theme provider wrapper for dark/light mode support### UI Features- **Gradient Backgrounds** - Beautiful orange-to-amber gradients- **Glass Morphism** - Modern frosted glass effects with backdrop blur- **Responsive Grid** - Adaptive layout for all screen sizes- **Loading States** - Smooth animations and progress indicators during processing- **Error Handling** - Comprehensive error messages and validation## DeploymentThe application is configured for deployment on Render.com:### Backend Deployment- **Service Type**: Web Service- **Environment**: Python- **Build Command**: `cd backend && pip install -r requirements.txt`- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`- **Environment Variables**: `REPLICATE_API_TOKEN` (set in Render dashboard)### Frontend Deployment- Deploy as a static site or web service- Set `BACKEND_URL` environment variable to your deployed backend URL- Build command: `cd frontend && npm install && npm run build`### Configuration Files- `render.yaml` - Render deployment configuration- `frontend/next.config.js` - Next.js configuration- `frontend/tsconfig.json` - TypeScript configuration## Environment Variables### Backend- `REPLICATE_API_TOKEN` - Your Replicate API token (required)- `PORT` - Server port (automatically set by Render)### Frontend- `BACKEND_URL` - Backend API URL (defaults to http://localhost:8000)- `NEXT_PUBLIC_*` - Any public environment variables## Error HandlingThe application includes comprehensive error handling:- **Prompt Validation**: Minimum 3 characters required- **API Key Validation**: Secure storage and validation- **Network Errors**: Graceful handling of connection issues- **Generation Failures**: Clear error messages for failed video generation- **File Download Errors**: Proper error handling for download failures## Dependencies### Backend Dependencies
fastapi==0.104.1 # Web framework uvicorn[standard]==0.24.0 # ASGI server replicate==0.22.0 # AI model integration python-multipart==0.0.6 # Form data handling python-dotenv==1.0.0 # Environment variables requests==2.31.0 # HTTP client

PlainText



### Frontend Dependencies- Next.js 14 with App Router- TypeScript for type safety- Tailwind CSS for styling- Lucide React for icons- React hooks for state management## Contributing1. Fork the repository2. Create a feature branch: `git checkout -b feature/amazing-feature`3. Commit your changes: `git commit -m 'Add amazing feature'`4. Push to the branch: `git push origin feature/amazing-feature`5. Open a Pull Request## LicenseThis project is licensed under the MIT License.## Troubleshooting### Common Issues1. **"REPLICATE_API_TOKEN not found"**   - Ensure your `.env` file is in the    backend directory   - Check that your API token is valid2. **CORS Errors**   - The backend is configured to allow    all origins   - Check that both frontend and backend    are running3. **Video Generation Fails**   - Verify your Replicate API token has    sufficient credits   - Check that your prompt meets the    minimum requirements4. **Build Errors**   - Ensure all dependencies are installed   - Check Node.js and Python versions## Author**Ayraf** - Made with ❤️---*Peppo AI - Where creativity meets artificial intelligence!***Live Demo**: [Your deployed URL here]**API Documentation**: [Your backend URL]/docs (FastAPI auto-generated docs)
