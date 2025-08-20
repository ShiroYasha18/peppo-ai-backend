import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json()
    console.log('Received request body:', body)
    
    // Validate required fields
    if (!body.prompt) {
      return NextResponse.json(
        { detail: 'Prompt is required' },
        { status: 400 }
      )
    }
    
    // Backend URL configuration
    const backendUrl = process.env.BACKEND_URL || 'https://peppo-ai-backend-1.onrender.com'
    console.log('Using backend URL:', backendUrl)
    
    // Make request to backend
    const response = await fetch(`${backendUrl}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })
    
    console.log('Backend response status:', response.status)
    console.log('Backend response headers:', Object.fromEntries(response.headers.entries()))
    
    // Handle non-OK responses
    if (!response.ok) {
      const contentType = response.headers.get('content-type') || ''
      console.log('Error response content-type:', contentType)
      
      if (contentType.includes('application/json')) {
        try {
          const errorData = await response.json()
          console.log('Backend JSON error:', errorData)
          return NextResponse.json(errorData, { status: response.status })
        } catch (jsonError) {
          console.error('Failed to parse error JSON:', jsonError)
          return NextResponse.json(
            { detail: `Backend error: ${response.status} ${response.statusText}` },
            { status: response.status }
          )
        }
      } else {
        // Handle HTML or other non-JSON responses
        const errorText = await response.text()
        console.error('Backend returned non-JSON error:', errorText.substring(0, 500))
        return NextResponse.json(
          { 
            detail: `Backend error: ${response.status} ${response.statusText}`,
            backend_response: errorText.substring(0, 200) + '...' 
          },
          { status: response.status }
        )
      }
    }
    
    // Handle successful response
    const contentType = response.headers.get('content-type') || ''
    if (!contentType.includes('application/json')) {
      const responseText = await response.text()
      console.error('Backend returned non-JSON success response:', responseText.substring(0, 500))
      return NextResponse.json(
        { detail: 'Backend returned invalid response format' },
        { status: 502 }
      )
    }
    
    try {
      const data = await response.json()
      console.log('Backend success response:', data)
      return NextResponse.json(data)
    } catch (jsonError) {
      console.error('Failed to parse success JSON:', jsonError)
      return NextResponse.json(
        { detail: 'Failed to parse backend response' },
        { status: 502 }
      )
    }
    
  } catch (error) {
    console.error('API route error:', error)
    
    // Handle different types of errors
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return NextResponse.json(
        { detail: 'Failed to connect to backend service' },
        { status: 503 }
      )
    }
    
    return NextResponse.json(
      { 
        detail: 'Internal server error',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}