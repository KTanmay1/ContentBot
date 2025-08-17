"use client"

import React, { useState, useEffect } from 'react'
import { useAppStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Activity,
  Server,
  Database,
  Cpu,
  MemoryStick,
  HardDrive,
  Wifi,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Eye,
  Pause,
  Play,
  X
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'

interface SystemMetrics {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_status: 'connected' | 'disconnected' | 'slow'
  active_workflows: number
  completed_workflows: number
  failed_workflows: number
  queue_size: number
  response_time: number
  uptime: string
}

interface WorkflowMetrics {
  total_workflows: number
  success_rate: number
  average_duration: number
  workflows_today: number
  workflows_this_week: number
  workflows_this_month: number
}

export default function MonitoringDashboard() {
  const { systemStatus, workflows, checkSystemHealth } = useAppStore()
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu_usage: 45,
    memory_usage: 62,
    disk_usage: 78,
    network_status: 'connected',
    active_workflows: 3,
    completed_workflows: 127,
    failed_workflows: 8,
    queue_size: 2,
    response_time: 245,
    uptime: '7d 14h 32m'
  })
  
  const [workflowMetrics, setWorkflowMetrics] = useState<WorkflowMetrics>({
    total_workflows: 135,
    success_rate: 94.1,
    average_duration: 180,
    workflows_today: 12,
    workflows_this_week: 45,
    workflows_this_month: 135
  })
  
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  const refreshMetrics = async () => {
    setIsRefreshing(true)
    try {
      await checkSystemHealth()
      // Simulate metrics update
      setSystemMetrics(prev => ({
        ...prev,
        cpu_usage: Math.max(10, Math.min(90, prev.cpu_usage + (Math.random() - 0.5) * 20)),
        memory_usage: Math.max(20, Math.min(95, prev.memory_usage + (Math.random() - 0.5) * 15)),
        response_time: Math.max(50, Math.min(500, prev.response_time + (Math.random() - 0.5) * 100))
      }))
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to refresh metrics:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    // Auto-refresh every 30 seconds
    const interval = setInterval(refreshMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'completed':
        return 'text-green-500'
      case 'warning':
      case 'slow':
      case 'running':
        return 'text-yellow-500'
      case 'error':
      case 'disconnected':
      case 'failed':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
      case 'completed':
        return CheckCircle
      case 'warning':
      case 'slow':
      case 'running':
        return AlertTriangle
      case 'error':
      case 'disconnected':
      case 'failed':
        return X
      default:
        return Clock
    }
  }

  const getUsageColor = (usage: number) => {
    if (usage > 80) return 'text-red-500'
    if (usage > 60) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getProgressColor = (usage: number) => {
    if (usage > 80) return 'bg-red-500'
    if (usage > 60) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center space-x-2">
            <Activity className="w-8 h-8 text-primary" />
            <span>System Monitoring</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor system health, performance metrics, and workflow statistics
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-muted-foreground">
            Last updated: {formatDate(lastUpdated)}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={refreshMetrics}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn("w-4 h-4 mr-2", isRefreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">System Status</p>
                <div className="flex items-center space-x-2 mt-1">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-lg font-semibold text-green-500">Healthy</span>
                </div>
              </div>
              <Server className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Workflows</p>
                <p className="text-2xl font-bold text-primary">{systemMetrics.active_workflows}</p>
              </div>
              <Activity className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Queue Size</p>
                <p className="text-2xl font-bold text-primary">{systemMetrics.queue_size}</p>
              </div>
              <Clock className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Response Time</p>
                <p className="text-2xl font-bold text-primary">{systemMetrics.response_time}ms</p>
              </div>
              <TrendingUp className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Resources */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Cpu className="w-5 h-5" />
              <span>System Resources</span>
            </CardTitle>
            <CardDescription>Real-time system resource utilization</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* CPU Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4" />
                  <span className="text-sm font-medium">CPU Usage</span>
                </div>
                <span className={cn("text-sm font-semibold", getUsageColor(systemMetrics.cpu_usage))}>
                  {systemMetrics.cpu_usage}%
                </span>
              </div>
              <Progress value={systemMetrics.cpu_usage} className="h-2" />
            </div>

            {/* Memory Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MemoryStick className="w-4 h-4" />
                  <span className="text-sm font-medium">Memory Usage</span>
                </div>
                <span className={cn("text-sm font-semibold", getUsageColor(systemMetrics.memory_usage))}>
                  {systemMetrics.memory_usage}%
                </span>
              </div>
              <Progress value={systemMetrics.memory_usage} className="h-2" />
            </div>

            {/* Disk Usage */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-4 h-4" />
                  <span className="text-sm font-medium">Disk Usage</span>
                </div>
                <span className={cn("text-sm font-semibold", getUsageColor(systemMetrics.disk_usage))}>
                  {systemMetrics.disk_usage}%
                </span>
              </div>
              <Progress value={systemMetrics.disk_usage} className="h-2" />
            </div>

            {/* Network Status */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center space-x-2">
                <Wifi className="w-4 h-4" />
                <span className="text-sm font-medium">Network</span>
              </div>
              <Badge variant={systemMetrics.network_status === 'connected' ? 'default' : 'destructive'}>
                {systemMetrics.network_status}
              </Badge>
            </div>

            {/* Uptime */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4" />
                <span className="text-sm font-medium">Uptime</span>
              </div>
              <span className="text-sm font-semibold text-primary">{systemMetrics.uptime}</span>
            </div>
          </CardContent>
        </Card>

        {/* Workflow Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5" />
              <span>Workflow Statistics</span>
            </CardTitle>
            <CardDescription>Performance metrics and success rates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Success Rate */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Success Rate</span>
                <span className="text-sm font-semibold text-green-500">
                  {workflowMetrics.success_rate}%
                </span>
              </div>
              <Progress value={workflowMetrics.success_rate} className="h-2" />
            </div>

            {/* Workflow Counts */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-green-500">{systemMetrics.completed_workflows}</div>
                <div className="text-xs text-muted-foreground">Completed</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold text-red-500">{systemMetrics.failed_workflows}</div>
                <div className="text-xs text-muted-foreground">Failed</div>
              </div>
            </div>

            {/* Time Periods */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Today</span>
                <span className="text-sm font-semibold">{workflowMetrics.workflows_today}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">This Week</span>
                <span className="text-sm font-semibold">{workflowMetrics.workflows_this_week}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">This Month</span>
                <span className="text-sm font-semibold">{workflowMetrics.workflows_this_month}</span>
              </div>
            </div>

            {/* Average Duration */}
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <span className="text-sm font-medium">Avg. Duration</span>
              <span className="text-sm font-semibold text-primary">
                {Math.floor(workflowMetrics.average_duration / 60)}m {workflowMetrics.average_duration % 60}s
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Workflows */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>Recent Workflows</span>
          </CardTitle>
          <CardDescription>Latest workflow executions and their status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {workflows.slice(0, 10).map((workflow) => {
              const StatusIcon = getStatusIcon(workflow.status)
              return (
                <div key={workflow.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <StatusIcon className={cn("w-5 h-5", getStatusColor(workflow.status))} />
                    <div>
                      <div className="font-medium">{workflow.type.replace('_', ' ').toUpperCase()}</div>
                      <div className="text-sm text-muted-foreground">
                        Started: {formatDate(new Date(workflow.createdAt))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <Badge variant={workflow.status === 'completed' ? 'default' : workflow.status === 'failed' ? 'destructive' : 'secondary'}>
                      {workflow.status}
                    </Badge>
                    {workflow.status === 'running' && (
                      <div className="flex items-center space-x-2">
                        <Progress value={workflow.progress} className="w-20 h-2" />
                        <span className="text-sm text-muted-foreground">{workflow.progress}%</span>
                      </div>
                    )}
                    <div className="flex space-x-1">
                      <Button variant="ghost" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      {workflow.status === 'running' && (
                        <Button variant="ghost" size="sm">
                          <Pause className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            
            {workflows.length === 0 && (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 mx-auto text-muted-foreground opacity-50 mb-4" />
                <h3 className="text-lg font-medium">No Recent Workflows</h3>
                <p className="text-muted-foreground">
                  Workflow activity will appear here once you start generating content
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}