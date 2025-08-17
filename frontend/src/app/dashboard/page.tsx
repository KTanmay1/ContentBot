"use client"

import React, { useEffect } from 'react'
import { useAppStore, ContentItem } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  FileText,
  MessageSquare,
  BarChart3,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Users,
  Zap,
  RefreshCw,
  Activity,
  Globe
} from 'lucide-react'
import Link from 'next/link'
import { formatDate } from '@/lib/utils'

export default function Dashboard() {
  const { 
    systemStatus, 
    workflows, 
    contents, 
    checkSystemHealth, 
    loadContents 
  } = useAppStore()

  useEffect(() => {
    checkSystemHealth()
    loadContents()
  }, [])

  const recentWorkflows = workflows.slice(0, 5)
  const recentContent = contents.slice(0, 5)
  const completedWorkflows = workflows.filter(w => w.status === 'completed').length
  const runningWorkflows = workflows.filter(w => w.status === 'running').length
  const totalContents = contents.length

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="space-y-8 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
              Dashboard
            </h1>
            <p className="text-lg text-muted-foreground">
              Welcome to ViraLearn ContentBot. Monitor your content generation and system health.
            </p>
          </div>
          <div className="flex space-x-3">
            <Link href="/blog">
              <Button size="lg" className="shadow-lg">
                <FileText className="w-5 h-5 mr-2" />
                Create Blog
              </Button>
            </Link>
            <Link href="/social">
              <Button variant="outline" size="lg" className="shadow-lg">
                <MessageSquare className="w-5 h-5 mr-2" />
                Social Media
              </Button>
            </Link>
            <Button 
              onClick={() => window.location.reload()}
              variant="ghost"
              size="lg"
              className="shadow-lg"
            >
              <RefreshCw className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-0 shadow-xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Content</CardTitle>
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700 dark:text-blue-300">{totalContents}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="w-3 h-3 mr-1 text-green-500" />
                +12% from last month
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
              <Zap className="h-5 w-5 text-green-600 dark:text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-700 dark:text-green-300">{runningWorkflows}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <Activity className="w-3 h-3 mr-1 text-green-500" />
                Currently processing
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-700 dark:text-purple-300">{completedWorkflows}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <CheckCircle className="w-3 h-3 mr-1 text-green-500" />
                Successfully finished
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-xl bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-950 dark:to-orange-900">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
              <Activity className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </CardHeader>
            <CardContent>
               <div className="text-3xl font-bold text-orange-700 dark:text-orange-300">
                 {systemStatus?.database === 'healthy' && systemStatus?.llm_provider === 'healthy' ? '100%' : '85%'}
               </div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <Globe className="w-3 h-3 mr-1 text-green-500" />
                All systems operational
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Workflows */}
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary" />
                Recent Workflows
              </CardTitle>
              <CardDescription>
                Latest content generation activities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentWorkflows.length > 0 ? (
                recentWorkflows.map((workflow) => (
                  <div key={workflow.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {workflow.type === 'blog_generation' ? (
                          <FileText className="h-5 w-5 text-blue-500" />
                        ) : (
                          <MessageSquare className="h-5 w-5 text-green-500" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium capitalize">
                          {workflow.type.replace('_', ' ')}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(workflow.createdAt)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge 
                        variant={workflow.status === 'completed' ? 'success' : 
                                workflow.status === 'running' ? 'default' : 'destructive'}
                        className="capitalize"
                      >
                        {workflow.status}
                      </Badge>
                      {workflow.progress !== undefined && (
                        <div className="w-16">
                          <Progress value={workflow.progress} className="h-2" />
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No recent workflows</p>
                  <p className="text-sm">Start creating content to see activity here</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Content */}
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Recent Content
              </CardTitle>
              <CardDescription>
                Your latest generated content
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {recentContent.length > 0 ? (
                 recentContent.map((item: ContentItem) => (
                  <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {item.type === 'blog' ? (
                          <FileText className="h-5 w-5 text-blue-500" />
                        ) : (
                          <MessageSquare className="h-5 w-5 text-green-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">
                          {item.title || 'Untitled Content'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(item.createdAt)}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline" className="capitalize">
                      {item.type}
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No content yet</p>
                  <p className="text-sm">Generate your first content to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Quick Actions
            </CardTitle>
            <CardDescription>
              Get started with content generation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link href="/blog" className="group">
                <div className="p-6 rounded-lg border-2 border-dashed border-muted-foreground/25 hover:border-primary hover:bg-primary/5 transition-all duration-300 cursor-pointer group-hover:shadow-lg">
                  <FileText className="w-8 h-8 text-primary mb-3 group-hover:scale-110 transition-transform" />
                  <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">Create Blog Post</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate engaging blog content with AI assistance
                  </p>
                </div>
              </Link>
              
              <Link href="/social" className="group">
                <div className="p-6 rounded-lg border-2 border-dashed border-muted-foreground/25 hover:border-primary hover:bg-primary/5 transition-all duration-300 cursor-pointer group-hover:shadow-lg">
                  <MessageSquare className="w-8 h-8 text-primary mb-3 group-hover:scale-110 transition-transform" />
                  <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">Social Media Post</h3>
                  <p className="text-sm text-muted-foreground">
                    Create compelling social media content for all platforms
                  </p>
                </div>
              </Link>
              
              <Link href="/monitoring" className="group">
                <div className="p-6 rounded-lg border-2 border-dashed border-muted-foreground/25 hover:border-primary hover:bg-primary/5 transition-all duration-300 cursor-pointer group-hover:shadow-lg">
                  <BarChart3 className="w-8 h-8 text-primary mb-3 group-hover:scale-110 transition-transform" />
                  <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">View Analytics</h3>
                  <p className="text-sm text-muted-foreground">
                    Monitor system performance and content metrics
                  </p>
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}