import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Proxy the request to our FastAPI backend
    const backendUrl = process.env.BACKEND_URL || 'https://peppo-ai-backend-1.onrender.com'
    
    const response = await fetch(`${backendUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      // Check if response is JSON before parsing
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json()
        return NextResponse.json(errorData, { status: response.status })
      } else {
        // Handle non-JSON error responses (like HTML error pages)
        const errorText = await response.text()
        console.error('Backend returned non-JSON error:', errorText)
        return NextResponse.json(
          { detail: `Backend error: ${response.status} ${response.statusText}` },
          { status: response.status }
        )
      }
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}