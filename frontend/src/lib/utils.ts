import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function encryptApiKey(key: string): string {
  return btoa(key)
}

export function decryptApiKey(encryptedKey: string): string {
  try {
    return atob(encryptedKey)
  } catch {
    return ''
  }
}

export function validateApiKey(key: string): boolean {
  return key.length > 10 && key.startsWith('r8_')
}