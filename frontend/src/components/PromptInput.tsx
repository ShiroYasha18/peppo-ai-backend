'use client'

import { useState } from 'react'
import { Lightbulb, Sparkles } from 'lucide-react'

interface PromptInputProps {
  prompt: string
  setPrompt: (prompt: string) => void
}

const EXAMPLE_PROMPTS = [
  "A majestic eagle soaring through misty mountain peaks at golden hour",
  "Ocean waves crashing against rocky cliffs during a dramatic sunset",
  "A bustling city street with neon lights reflecting on wet pavement at night",
  "Cherry blossoms falling gently in a peaceful Japanese garden",
  "Northern lights dancing across a starry sky over a snowy landscape",
  "A cozy campfire crackling in a forest clearing under the stars"
]

export default function PromptInput({ prompt, setPrompt }: PromptInputProps) {
  const [showExamples, setShowExamples] = useState(false)
  const maxLength = 500
  const remainingChars = maxLength - prompt.length
  
  const handlePromptChange = (value: string) => {
    if (value.length <= maxLength) {
      setPrompt(value)
    }
  }

  const useExamplePrompt = (examplePrompt: string) => {
    setPrompt(examplePrompt)
    setShowExamples(false)
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <textarea
          value={prompt}
          onChange={(e) => handlePromptChange(e.target.value)}
          placeholder="Describe the video you want to generate... Be creative and detailed!"
          className="w-full p-4 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:outline-none transition-colors resize-none text-lg"
          rows={4}
        />
        
        <div className="absolute bottom-3 right-3 flex items-center gap-3">
          <span className={`text-sm font-medium ${
            remainingChars < 50 ? 'text-red-500' : 
            remainingChars < 100 ? 'text-yellow-500' : 
            'text-gray-500'
          }`}>
            {remainingChars} characters left
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Sparkles className="w-4 h-4" />
          <span>Tip: Be specific about lighting, movement, and atmosphere</span>
        </div>
        
        <button
          onClick={() => setShowExamples(!showExamples)}
          className="flex items-center gap-2 px-3 py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
        >
          <Lightbulb className="w-4 h-4" />
          {showExamples ? 'Hide Examples' : 'Show Examples'}
        </button>
      </div>

      {showExamples && (
        <div className="bg-gray-50 rounded-xl p-4 space-y-3">
          <h4 className="font-medium text-gray-700 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Example Prompts
          </h4>
          <div className="grid gap-2">
            {EXAMPLE_PROMPTS.map((example, index) => (
              <button
                key={index}
                onClick={() => useExamplePrompt(example)}
                className="text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition-all text-sm"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}