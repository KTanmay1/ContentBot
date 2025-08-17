"use client"

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store'
import {
  Home,
  FileText,
  MessageSquare,
  BarChart3,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
  LayoutDashboard
} from 'lucide-react'
import { Button } from '@/components/ui/button'

const navigation = [
  {
    name: 'Home',
    href: '/',
    icon: Home
  },
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard
  },
  {
    name: 'Blog Generator',
    href: '/blog',
    icon: FileText
  },
  {
    name: 'Social Media',
    href: '/social',
    icon: MessageSquare
  },
  {
    name: 'Monitoring',
    href: '/monitoring',
    icon: BarChart3
  },
  {
    name: 'History',
    href: '/history',
    icon: History
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings
  }
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, setSidebarOpen } = useAppStore()

  return (
    <div
      className={cn(
        'flex flex-col h-full bg-card border-r border-border transition-all duration-300 ease-in-out',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className={cn('flex items-center space-x-2', !sidebarOpen && 'justify-center')}>
          <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
            <Bot className="w-5 h-5 text-primary-foreground" />
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <h1 className="text-lg font-semibold text-foreground">ViraLearn</h1>
              <p className="text-xs text-muted-foreground">ContentBot</p>
            </div>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="h-8 w-8"
        >
          {sidebarOpen ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          const Icon = item.icon

          return (
            <Link key={item.name} href={item.href}>
              <div
                className={cn(
                  'flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent',
                  !sidebarOpen && 'justify-center'
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && <span>{item.name}</span>}
              </div>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className={cn('flex items-center space-x-2', !sidebarOpen && 'justify-center')}>
          <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
            <span className="text-xs font-medium">AI</span>
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <p className="text-sm font-medium">AI Assistant</p>
              <p className="text-xs text-muted-foreground">Online</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}