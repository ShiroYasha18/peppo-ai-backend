export interface VideoGenerationParams {
  prompt: string
  fps: number
  duration: number
  resolution: '480p' | '720p' | '1080p'
  aspectRatio: '16:9' | '9:16' | '1:1'
  cameraFixed: boolean
}

export interface GenerationResponse {
  video_url: string
  message: string
  prompt_used: string
  duration: string
  resolution: string
}

export interface ApiKeyState {
  key: string
  isValid: boolean
  isVisible: boolean
}