'use client'

import { useState, useEffect } from 'react'
import { Eye, EyeOff, Key, CheckCircle, XCircle } from 'lucide-react'
import { ApiKeyState } from '@/types'
import { encryptApiKey, decryptApiKey, validateApiKey } from '@/lib/utils'

interface ApiKeyInputProps {
  apiKey: ApiKeyState
  setApiKey: (apiKey: ApiKeyState) => void
}

export default function ApiKeyInput({ apiKey, setApiKey }: ApiKeyInputProps) {
  useEffect(() => {
    // Load API key from localStorage on mount
    const savedKey = localStorage.getItem('peppo_api_key')
    if (savedKey) {
      const decryptedKey = decryptApiKey(savedKey)
      setApiKey({
        key: decryptedKey,
        isValid: validateApiKey(decryptedKey),
        isVisible: false
      })
    }
  }, [])

  const handleKeyChange = (value: string) => {
    const isValid = validateApiKey(value)
    setApiKey({
      key: value,
      isValid,
      isVisible: apiKey.isVisible
    })

    // Save to localStorage if valid
    if (isValid) {
      localStorage.setItem('peppo_api_key', encryptApiKey(value))
    } else {
      localStorage.removeItem('peppo_api_key')
    }
  }

  const toggleVisibility = () => {
    setApiKey({
      ...apiKey,
      isVisible: !apiKey.isVisible
    })
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
          <Key className="w-5 h-5 text-gray-400" />
        </div>
        
        <input
          type={apiKey.isVisible ? 'text' : 'password'}
          value={apiKey.key}
          onChange={(e) => handleKeyChange(e.target.value)}
          placeholder="Enter your Replicate API key (r8_...)"
          className="w-full pl-12 pr-20 py-4 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:outline-none transition-colors text-lg"
        />
        
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
          <button
            onClick={toggleVisibility}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {apiKey.isVisible ? (
              <EyeOff className="w-5 h-5 text-gray-400" />
            ) : (
              <Eye className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          {apiKey.key && (
            <div className="flex items-center">
              {apiKey.isValid ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="text-sm text-gray-600">
        {!apiKey.key && (
          <p>🔑 Get your API key from <a href="https://replicate.com" target="_blank" className="text-purple-600 hover:underline">replicate.com</a></p>
        )}
        {apiKey.key && !apiKey.isValid && (
          <p className="text-red-600">❌ Invalid API key format. Should start with 'r8_'</p>
        )}
        {apiKey.isValid && (
          <p className="text-green-600">✅ API key is valid and securely stored</p>
        )}
      </div>
    </div>
  )
}