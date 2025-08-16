import type { Metadata } from 'next'
import './globals.css'
import ClientWrapper from '@/components/ClientWrapper'

export const metadata: Metadata = {
  title: 'Peppo AI - Friendly Video Generator',
  description: 'Create amazing videos with AI - Simple, Fast, and Fun!',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="font-sans">
        <ClientWrapper>
          {children}
        </ClientWrapper>
      </body>
    </html>
  )
}