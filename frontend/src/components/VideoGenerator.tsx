'use client'

import { useState } from 'react'
import { Play, Download, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { VideoGenerationParams, GenerationResponse } from '@/types'

interface VideoGeneratorProps {
  apiKey: string
  params: VideoGenerationParams
  isApiKeyValid: boolean
}

type GenerationState = 'idle' | 'generating' | 'success' | 'error'

export default function VideoGenerator({ apiKey, params, isApiKeyValid }: VideoGeneratorProps) {
  const [generationState, setGenerationState] = useState<GenerationState>('idle')
  const [generationResponse, setGenerationResponse] = useState<GenerationResponse | null>(null)
  const [error, setError] = useState<string>('')
  const [progress, setProgress] = useState(0)

  const generateVideo = async () => {
    if (!isApiKeyValid || !params.prompt.trim()) {
      setError('Please provide a valid API key and prompt')
      return
    }

    setGenerationState('generating')
    setError('')
    setProgress(0)

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + Math.random() * 15
      })
    }, 1000)

    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey, // Fixed: removed .key since apiKey is already a string
          prompt: params.prompt,
          fps: params.fps,
          duration: params.duration,
          resolution: params.resolution,
          aspect_ratio: params.aspectRatio,
          camera_fixed: params.cameraFixed
        })
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate video')
      }

      const data: GenerationResponse = await response.json()
      setGenerationResponse(data)
      setGenerationState('success')
    } catch (err) {
      clearInterval(progressInterval)
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
      setGenerationState('error')
      setProgress(0)
    }
  }

  const downloadVideo = async () => {
    if (!generationResponse?.video_url) return

    try {
      const response = await fetch(generationResponse.video_url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `peppo-video-${Date.now()}.mp4`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Failed to download video')
    }
  }

  const resetGeneration = () => {
    setGenerationState('idle')
    setGenerationResponse(null)
    setError('')
    setProgress(0)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border-2 border-gray-200 dark:border-gray-700">
      <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-6">Generate Video</h3>
      
      {/* Idle State */}
      {generationState === 'idle' && (
        <div className="text-center">
          <div className="mb-6">
            <div className="w-24 h-24 mx-auto bg-gradient-to-r from-orange-500 to-amber-500 rounded-full flex items-center justify-center mb-4">
              <Play className="w-12 h-12 text-white" />
            </div>
            <p className="text-gray-600 dark:text-gray-300">
              Ready to create your video! Make sure you have a valid API key and prompt.
            </p>
          </div>
          
          <button
            onClick={generateVideo}
            disabled={!isApiKeyValid || !params.prompt.trim()}
            className="w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white py-4 px-6 rounded-xl font-semibold text-lg hover:from-orange-600 hover:to-amber-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          >
            <Play className="w-6 h-6" />
            Generate Video
          </button>
        </div>
      )}

      {/* Generating State */}
      {generationState === 'generating' && (
        <div className="text-center">
          <div className="mb-6">
            <div className="w-24 h-24 mx-auto bg-gradient-to-r from-orange-500 to-amber-500 rounded-full flex items-center justify-center mb-4">
              <Loader2 className="w-12 h-12 text-white animate-spin" />
            </div>
            <h4 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
              Creating your video...
            </h4>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              This may take a few minutes. Please don't close this page.
            </p>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-2">
              <div 
                className="bg-gradient-to-r from-orange-500 to-amber-500 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {Math.round(progress)}% complete
            </p>
          </div>
        </div>
      )}

      {/* Success State */}
      {generationState === 'success' && generationResponse && (
        <div className="space-y-6">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto bg-green-500 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-green-800 dark:text-green-400 mb-2">
              Video Generated Successfully!
            </h4>
          </div>
          
          {/* Video Preview */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <video 
              src={generationResponse.video_url} 
              controls 
              className="w-full rounded-lg"
              poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'%3E%3Crect width='400' height='300' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%236b7280'%3EVideo Preview%3C/text%3E%3C/svg%3E"
            />
          </div>
          
          {/* Video Details */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="font-medium text-gray-600 dark:text-gray-300">Prompt:</span>
              <span className="ml-2 text-gray-800 dark:text-white">{generationResponse.prompt_used}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-gray-600 dark:text-gray-300">Duration:</span>
              <span className="ml-2 text-gray-800 dark:text-white">{generationResponse.duration}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium text-gray-600 dark:text-gray-300">Resolution:</span>
              <span className="ml-2 text-gray-800 dark:text-white">{generationResponse.resolution}</span>
            </div>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={downloadVideo}
              className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Download Video
            </button>
            <button
              onClick={resetGeneration}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Generate Another
            </button>
          </div>
        </div>
      )}

      {/* Error State */}
      {generationState === 'error' && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border-2 border-red-200 dark:border-red-800">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            <h3 className="font-semibold text-red-800 dark:text-red-400">Generation Failed</h3>
          </div>
          <p className="text-red-700 dark:text-red-300 mb-4">{error}</p>
          <button
            onClick={resetGeneration}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  )
}