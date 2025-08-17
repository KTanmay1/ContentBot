"use client"

import React, { useEffect } from 'react'
import { Sidebar } from './sidebar'
import { Header } from './header'
import { useAppStore } from '@/store'
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { sidebarOpen, checkSystemHealth, loadContents } = useAppStore()

  // Initialize app data on mount
  useEffect(() => {
    const initializeApp = async () => {
      try {
        await Promise.all([
          checkSystemHealth(),
          loadContents()
        ])
      } catch (error) {
        console.error('Failed to initialize app:', error)
      }
    }

    initializeApp()

    // Set up periodic health checks
    const healthCheckInterval = setInterval(() => {
      checkSystemHealth()
    }, 30000) // Check every 30 seconds

    return () => clearInterval(healthCheckInterval)
  }, [checkSystemHealth, loadContents])

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />
        
        {/* Page Content */}
        <main 
          className={cn(
            'flex-1 overflow-auto p-6 transition-all duration-300 ease-in-out',
            'bg-gradient-to-br from-background to-muted/20'
          )}
        >
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}