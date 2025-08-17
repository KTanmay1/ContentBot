"use client"

import React from 'react'
import { useAppStore, useSystemStatus, useActiveWorkflow } from '@/store'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Bell,
  Settings,
  User,
  Wifi,
  WifiOff,
  AlertCircle,
  CheckCircle,
  Pause,
  Play,
  X
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function Header() {
  const systemStatus = useSystemStatus()
  const activeWorkflow = useActiveWorkflow()
  const { pauseWorkflow, resumeWorkflow, cancelWorkflow } = useAppStore()

  const isSystemHealthy = systemStatus && 
    systemStatus.database === 'healthy' && 
    systemStatus.llm_provider === 'healthy'

  const handleWorkflowAction = async (action: 'pause' | 'resume' | 'cancel') => {
    if (!activeWorkflow) return
    
    try {
      switch (action) {
        case 'pause':
          await pauseWorkflow(activeWorkflow.id)
          break
        case 'resume':
          await resumeWorkflow(activeWorkflow.id)
          break
        case 'cancel':
          await cancelWorkflow(activeWorkflow.id)
          break
      }
    } catch (error) {
      console.error(`Failed to ${action} workflow:`, error)
    }
  }

  return (
    <header className="h-16 bg-background border-b border-border flex items-center justify-between px-6">
      {/* Left side - System Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          {isSystemHealthy ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-sm text-muted-foreground">System Online</span>
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-red-500" />
              <span className="text-sm text-muted-foreground">System Issues</span>
            </>
          )}
        </div>

        {/* Active Workflow Status */}
        {activeWorkflow && (
          <div className="flex items-center space-x-3 px-3 py-1 bg-muted rounded-lg">
            <div className="flex items-center space-x-2">
              {activeWorkflow.status === 'running' && (
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              )}
              {activeWorkflow.status === 'paused' && (
                <div className="w-2 h-2 bg-yellow-500 rounded-full" />
              )}
              {activeWorkflow.status === 'failed' && (
                <div className="w-2 h-2 bg-red-500 rounded-full" />
              )}
              {activeWorkflow.status === 'completed' && (
                <div className="w-2 h-2 bg-green-500 rounded-full" />
              )}
              <span className="text-sm font-medium capitalize">
                {activeWorkflow.type} - {activeWorkflow.status}
              </span>
            </div>
            
            {activeWorkflow.status === 'running' && (
              <div className="flex items-center space-x-2">
                <Progress value={activeWorkflow.progress} className="w-20 h-2" />
                <span className="text-xs text-muted-foreground">
                  {activeWorkflow.progress}%
                </span>
              </div>
            )}
            
            {/* Workflow Controls */}
            <div className="flex items-center space-x-1">
              {activeWorkflow.status === 'running' && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => handleWorkflowAction('pause')}
                >
                  <Pause className="h-3 w-3" />
                </Button>
              )}
              {activeWorkflow.status === 'paused' && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => handleWorkflowAction('resume')}
                >
                  <Play className="h-3 w-3" />
                </Button>
              )}
              {(activeWorkflow.status === 'running' || activeWorkflow.status === 'paused') && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-red-500 hover:text-red-600"
                  onClick={() => handleWorkflowAction('cancel')}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right side - User Actions */}
      <div className="flex items-center space-x-3">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
            2
          </span>
        </Button>

        {/* Settings */}
        <Button variant="ghost" size="icon">
          <Settings className="h-4 w-4" />
        </Button>

        {/* User Profile */}
        <Button variant="ghost" size="icon">
          <User className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}