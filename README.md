# Peppo AI 🎬✨

> Transform your ideas into stunning videos with AI magic! Simple, fast, and incredibly fun to use.

## Demo

### Video Demo

**[📹 Watch Demo Video](./demovid.mov)**

*Click the link above to download and view the demo video showing Peppo AI in action!*

> **Note**: The demo video is in `.mov` format. For better web compatibility, consider converting to `.mp4` or `.gif` format, or upload to a video hosting service like YouTube or Vimeo for embedded preview.
[🚀 Live Demo](https://peppo-ai-frontendd.onrender.com/) • 
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

## Quick Start

### 🚀 One-Command Setup

```bash
# Clone and setup the entire project
git clone <your-repo-url>
cd peppo

# Setup backend
cd backend
pip install -r requirements.txt
echo "REPLICATE_API_TOKEN=your_token_here" > .env
uvicorn main:app --reload --port 8000 &

# Setup frontend
cd ../frontend
npm install
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser!

## API Endpoints

### POST /generate
Generate a video from a text prompt with custom parameters.

**Request Body:**
```json
{
  "api_key": "string (optional)",
  "prompt": "string (required, min 3 chars)",
  "fps": "integer (optional, default: 24)",
  "duration": "integer (optional, default: 5, max: 10)",
  "resolution": "string (optional, default: '720p', options: '720p'|'1080p')",
  "aspect_ratio": "string (optional, default: '16:9', options: '16:9'|'9:16'|'1:1')",
  "camera_fixed": "boolean (optional, default: false)"
}
```

**Response:**
```json
{
  "video_url": "string",
  "message": "Video generated successfully",
  "prompt_used": "string",
  "duration": "string",
  "resolution": "string",
  "fps": "integer",
  "aspect_ratio": "string",
  "camera_fixed": "boolean"
}
```

### POST /generate-download
Generate and directly download a video file.

**Request Body:**
```json
{
  "prompt": "string (required, min 3 chars)"
}
```

**Response:** Direct MP4 file download

### GET /
Health check endpoint.

**Response:**
```json
{
  "message": "Video Generation API is running!"
}
```

## Environment Setup

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.8+**
- **Replicate API token** (get one at [replicate.com](https://replicate.com))

### Backend Configuration

1. Create environment file:
   ```bash
   cd backend
   touch .env
   ```

2. Add your Replicate API token:
   ```env
   REPLICATE_API_TOKEN=r8_your_actual_token_here
   ```

### Frontend Configuration

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. (Optional) Set backend URL:
   ```bash
   echo "BACKEND_URL=http://localhost:8000" > .env.local
   ```

## Usage Guide

### Step-by-Step Video Generation

1. **🔑 API Key Setup**
   - Enter your Replicate API key in the secure input field
   - The key is stored locally and validated automatically

2. **✍️ Write Your Prompt**
   - Describe the video you want to create
   - Minimum 3 characters required
   - Be descriptive for better results!

3. **⚙️ Customize Parameters**
   - **FPS**: Frame rate (default: 24)
   - **Duration**: Video length 1-10 seconds (default: 5)
   - **Resolution**: 720p or 1080p (default: 720p)
   - **Aspect Ratio**: 16:9, 9:16, or 1:1 (default: 16:9)
   - **Camera Fixed**: Stationary vs. moving camera (default: moving)

4. **🎬 Generate & Download**
   - Click "Generate Video" and wait for the magic
   - Preview your video in the built-in player
   - Download directly to your device

### Example Prompts

- "A serene sunset over a calm ocean with gentle waves"
- "A bustling city street at night with neon lights"
- "A cute cat playing with a ball of yarn in slow motion"
- "Abstract colorful particles floating in space"

## Components Architecture

### Core Components
- **ApiKeyInput** - Secure API key management with validation and visibility toggle
- **PromptInput** - Text area with character counting and validation
- **ParameterSliders** - Interactive controls for all video parameters
- **VideoGenerator** - Main generation interface with progress tracking
- **ClientWrapper** - Theme provider for consistent styling

### UI Features
- **Glass Morphism** - Modern frosted glass effects with backdrop blur
- **Gradient Backgrounds** - Beautiful orange-to-amber gradients
- **Responsive Design** - Mobile-first approach with adaptive layouts
- **Loading States** - Smooth animations and progress indicators
- **Error Handling** - User-friendly error messages and validation

## Deployment

### Render.com Deployment

The project is pre-configured for Render.com deployment:

#### Backend Service
```yaml
services:
  - type: web
    name: peppo-ai-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: REPLICATE_API_TOKEN
        sync: false
```

#### Frontend Service
- Deploy as a static site
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/out` or `frontend/.next`

### Environment Variables

#### Backend
- `REPLICATE_API_TOKEN` - Your Replicate API token (**required**)
- `PORT` - Server port (auto-set by Render)

#### Frontend
- `BACKEND_URL` - Backend API URL (defaults to localhost:8000)

## Troubleshooting

### Common Issues & Solutions

#### 🔴 "REPLICATE_API_TOKEN not found"
**Solution:**
```bash
# Check your .env file exists and has the correct token
cd backend
cat .env
# Should show: REPLICATE_API_TOKEN=r8_your_token_here
```

#### 🔴 CORS Errors
**Solution:**
- Ensure both frontend (port 3000) and backend (port 8000) are running
- Check that BACKEND_URL points to the correct backend URL

#### 🔴 Video Generation Fails
**Solutions:**
- Verify your Replicate API token has sufficient credits
- Check prompt meets minimum 3-character requirement
- Try simpler prompts if complex ones fail

#### 🔴 Build/Deployment Errors
**Solutions:**
```bash
# Clear caches and reinstall
cd frontend
rm -rf node_modules package-lock.json .next
npm install
npm run build

# For backend
cd backend
pip install --upgrade -r requirements.txt
```

## Dependencies

### Backend Dependencies
```txt
fastapi==0.104.1          # Modern web framework
uvicorn[standard]==0.24.0 # ASGI server with performance extras
replicate==0.22.0         # AI model integration
python-multipart==0.0.6   # Form data handling
python-dotenv==1.0.0      # Environment variable management
requests==2.31.0          # HTTP client for file downloads
```

### Frontend Dependencies
- **Next.js 14** - Latest React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, customizable icons

## Contributing

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone <your-fork-url>
   cd peppo
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

4. **Test Locally**
   ```bash
   # Test backend
   cd backend && python -m pytest
   
   # Test frontend
   cd frontend && npm run build
   ```

5. **Submit PR**
   ```bash
   git commit -m 'Add amazing feature'
   git push origin feature/amazing-feature
   ```

### Code Style
- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: Use Prettier and ESLint configurations
- **Commits**: Use conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 **Email**: [your-email@example.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/peppo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/peppo/discussions)

## Roadmap

- [ ] Add more AI models (Stable Video Diffusion, etc.)
- [ ] Implement user authentication and video history
- [ ] Add batch video generation
- [ ] Support for longer video durations
- [ ] Video editing capabilities
- [ ] Social sharing features

## Author

**Ayraf** - *Full Stack Developer*

- GitHub: [@ayrafraihan](https://github.com/ayrafraihan)
- Made with ❤️ and lots of ☕

---
