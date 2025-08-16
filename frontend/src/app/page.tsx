'use client'

import { useState } from 'react'
import { VideoGenerationParams, ApiKeyState } from '@/types'
import ApiKeyInput from '@/components/ApiKeyInput'
import PromptInput from '@/components/PromptInput'
import ParameterSliders from '@/components/ParameterSliders'
import VideoGenerator from '@/components/VideoGenerator'
import ThemeToggle from '../components/ThemeToggle'
import { Sparkles, Video } from 'lucide-react'

export default function Home() {
  const [apiKey, setApiKey] = useState<ApiKeyState>({
    key: '',
    isValid: false,
    isVisible: false
  })
  
  const [params, setParams] = useState<VideoGenerationParams>({
    prompt: '',
    fps: 24,
    duration: 5,
    resolution: '720p',
    aspectRatio: '16:9',
    cameraFixed: false
  })

  const setPrompt = (prompt: string) => {
    setParams(prev => ({ ...prev, prompt }))
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 dark:from-gray-900 dark:via-black dark:to-gray-800">
      {/* Theme Toggle - Fixed position in top right */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-500">
              <Video className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold gradient-text">
              Peppo AI
            </h1>
            <Sparkles className="w-8 h-8 text-orange-500 dark:text-orange-400" />
          </div>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Transform your ideas into stunning videos with AI magic! 
            Simple, fast, and incredibly fun to use.
          </p>
        </div>

        {/* API Key Input */}
        <div className="mb-8">
          <ApiKeyInput apiKey={apiKey} setApiKey={setApiKey} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column */}
          <div className="space-y-6">
            <PromptInput prompt={params.prompt} setPrompt={setPrompt} />
            <ParameterSliders params={params} setParams={setParams} />
          </div>

          {/* Right Column */}
          <div>
            <VideoGenerator 
              apiKey={apiKey.key}
              params={params}
              isApiKeyValid={apiKey.isValid}
            />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-gray-500 dark:text-gray-400">
          <p>Made with ❤️ by Ayraf</p>
        </footer>
      </div>
    </div>
  )
}