'use client'

import { VideoGenerationParams } from '@/types'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'

interface ParameterSlidersProps {
  params: VideoGenerationParams
  setParams: (params: VideoGenerationParams) => void
}

export default function ParameterSliders({ params, setParams }: ParameterSlidersProps) {
  const updateParam = (key: keyof VideoGenerationParams, value: any) => {
    setParams({ ...params, [key]: value })
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border-2 border-gray-200 dark:border-gray-700 space-y-6">
      <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">Video Parameters</h3>
      
      {/* FPS Slider */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          FPS: {params.fps}
        </label>
        <Slider
          value={[params.fps]}
          onValueChange={(value) => updateParam('fps', value[0])}
          max={60}
          min={24}
          step={1}
          className="w-full"
        />
      </div>

      {/* Duration Slider */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Duration: {params.duration}s
        </label>
        <Slider
          value={[params.duration]}
          onValueChange={(value) => updateParam('duration', value[0])}
          max={10}
          min={5}
          step={1}
          className="w-full"
        />
      </div>

      {/* Resolution Select */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Resolution
        </label>
        <select
          value={params.resolution}
          onChange={(e) => updateParam('resolution', e.target.value)}
          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="480p">480p</option>
          <option value="720p">720p</option>
          <option value="1080p">1080p</option>
        </select>
      </div>

      {/* Aspect Ratio Select */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Aspect Ratio
        </label>
        <select
          value={params.aspectRatio}
          onChange={(e) => updateParam('aspectRatio', e.target.value)}
          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="16:9">16:9 (Landscape)</option>
          <option value="9:16">9:16 (Portrait)</option>
          <option value="1:1">1:1 (Square)</option>
        </select>
      </div>

      {/* Camera Fixed Toggle */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Fixed Camera
        </label>
        <Switch
          checked={params.cameraFixed}
          onCheckedChange={(checked) => updateParam('cameraFixed', checked)}
        />
      </div>
    </div>
  )
}