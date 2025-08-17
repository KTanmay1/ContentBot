"use client"

import React, { useState, useEffect } from 'react'
import { useAppStore } from '@/store'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  History,
  Search,
  Filter,
  Download,
  Eye,
  Trash2,
  Calendar,
  Clock,
  FileText,
  MessageSquare,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  RotateCcw,
  MoreHorizontal,
  SortAsc,
  SortDesc
} from 'lucide-react'
import { cn, formatDate } from '@/lib/utils'

type FilterType = 'all' | 'blog' | 'social'
type StatusFilter = 'all' | 'completed' | 'failed' | 'running' | 'paused' | 'cancelled'
type SortBy = 'date' | 'type' | 'status'
type SortOrder = 'asc' | 'desc'

export default function HistoryPage() {
  const { workflows, contents, removeWorkflow, removeContent } = useAppStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState<FilterType>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [sortBy, setSortBy] = useState<SortBy>('date')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<'workflows' | 'content'>('workflows')

  // Filter and sort workflows
  const filteredWorkflows = workflows
    .filter(workflow => {
      const matchesSearch = workflow.type.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesType = typeFilter === 'all' || 
        (typeFilter === 'blog' && workflow.type.includes('blog')) ||
        (typeFilter === 'social' && workflow.type.includes('social'))
      const matchesStatus = statusFilter === 'all' || workflow.status === statusFilter
      return matchesSearch && matchesType && matchesStatus
    })
    .sort((a, b) => {
      let comparison = 0
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
          break
        case 'type':
          comparison = a.type.localeCompare(b.type)
          break
        case 'status':
          comparison = a.status.localeCompare(b.status)
          break
      }
      return sortOrder === 'asc' ? comparison : -comparison
    })

  // Filter and sort content
  const filteredContent = contents
    .filter(content => {
      const matchesSearch = content.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        content.content.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesType = typeFilter === 'all' || content.type === typeFilter
      return matchesSearch && matchesType
    })
    .sort((a, b) => {
      let comparison = 0
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
          break
        case 'type':
          comparison = a.type.localeCompare(b.type)
          break
        default:
          comparison = a.title.localeCompare(b.title)
      }
      return sortOrder === 'asc' ? comparison : -comparison
    })

  const handleSelectItem = (id: string) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedItems(newSelected)
  }

  const handleSelectAll = () => {
    const currentItems = activeTab === 'workflows' ? filteredWorkflows : filteredContent
    if (selectedItems.size === currentItems.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(currentItems.map(item => item.id)))
    }
  }

  const handleDeleteSelected = () => {
    if (confirm(`Are you sure you want to delete ${selectedItems.size} selected items?`)) {
      selectedItems.forEach(id => {
        if (activeTab === 'workflows') {
          removeWorkflow(id)
        } else {
          removeContent(id)
        }
      })
      setSelectedItems(new Set())
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle
      case 'failed':
        return XCircle
      case 'running':
        return Play
      case 'paused':
        return Pause
      case 'cancelled':
        return RotateCcw
      default:
        return Clock
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-500'
      case 'failed':
        return 'text-red-500'
      case 'running':
        return 'text-blue-500'
      case 'paused':
        return 'text-yellow-500'
      case 'cancelled':
        return 'text-gray-500'
      default:
        return 'text-gray-500'
    }
  }

  const getTypeIcon = (type: string) => {
    if (type.includes('blog')) return FileText
    if (type.includes('social')) return MessageSquare
    return FileText
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center space-x-2">
            <History className="w-8 h-8 text-primary" />
            <span>History</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage your workflow history and generated content
          </p>
        </div>
        {selectedItems.size > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">
              {selectedItems.size} selected
            </span>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDeleteSelected}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Selected
            </Button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('workflows')}
          className={cn(
            "px-4 py-2 rounded-md text-sm font-medium transition-colors",
            activeTab === 'workflows'
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Workflows ({workflows.length})
        </button>
        <button
          onClick={() => setActiveTab('content')}
          className={cn(
            "px-4 py-2 rounded-md text-sm font-medium transition-colors",
            activeTab === 'content'
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Content ({contents.length})
        </button>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search workflows and content..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Type Filter */}
            <Select value={typeFilter} onValueChange={(value: FilterType) => setTypeFilter(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="blog">Blog Posts</SelectItem>
                <SelectItem value="social">Social Media</SelectItem>
              </SelectContent>
            </Select>

            {/* Status Filter (only for workflows) */}
            {activeTab === 'workflows' && (
              <Select value={statusFilter} onValueChange={(value: StatusFilter) => setStatusFilter(value)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            )}

            {/* Sort */}
            <Select value={sortBy} onValueChange={(value: SortBy) => setSortBy(value)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date">Date</SelectItem>
                <SelectItem value="type">Type</SelectItem>
                {activeTab === 'workflows' && <SelectItem value="status">Status</SelectItem>}
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              {activeTab === 'workflows' ? 'Workflow History' : 'Generated Content'}
            </CardTitle>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedItems.size > 0 && selectedItems.size === (activeTab === 'workflows' ? filteredWorkflows : filteredContent).length}
                onChange={handleSelectAll}
                className="rounded"
              />
              <span className="text-sm text-muted-foreground">Select All</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeTab === 'workflows' ? (
              filteredWorkflows.length > 0 ? (
                filteredWorkflows.map((workflow) => {
                  const StatusIcon = getStatusIcon(workflow.status)
                  const TypeIcon = getTypeIcon(workflow.type)
                  return (
                    <div key={workflow.id} className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-muted/50">
                      <input
                        type="checkbox"
                        checked={selectedItems.has(workflow.id)}
                        onChange={() => handleSelectItem(workflow.id)}
                        className="rounded"
                      />
                      <div className="flex items-center space-x-3 flex-1">
                        <TypeIcon className="w-5 h-5 text-muted-foreground" />
                        <div className="flex-1">
                          <div className="font-medium">
                            {workflow.type.replace('_', ' ').toUpperCase()}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {formatDate(workflow.createdAt)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                          <StatusIcon className={cn("w-4 h-4", getStatusColor(workflow.status))} />
                          <Badge variant={workflow.status === 'completed' ? 'default' : workflow.status === 'failed' ? 'destructive' : 'secondary'}>
                            {workflow.status}
                          </Badge>
                        </div>
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
                          <Button variant="ghost" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => removeWorkflow(workflow.id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-8">
                  <History className="w-12 h-12 mx-auto text-muted-foreground opacity-50 mb-4" />
                  <h3 className="text-lg font-medium">No Workflows Found</h3>
                  <p className="text-muted-foreground">
                    {searchTerm || typeFilter !== 'all' || statusFilter !== 'all'
                      ? 'Try adjusting your filters or search terms'
                      : 'Your workflow history will appear here once you start generating content'}
                  </p>
                </div>
              )
            ) : (
              filteredContent.length > 0 ? (
                filteredContent.map((content) => {
                  const TypeIcon = getTypeIcon(content.type)
                  return (
                    <div key={content.id} className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-muted/50">
                      <input
                        type="checkbox"
                        checked={selectedItems.has(content.id)}
                        onChange={() => handleSelectItem(content.id)}
                        className="rounded"
                      />
                      <div className="flex items-center space-x-3 flex-1">
                        <TypeIcon className="w-5 h-5 text-muted-foreground" />
                        <div className="flex-1">
                          <div className="font-medium">{content.title}</div>
                          <div className="text-sm text-muted-foreground line-clamp-2">
                            {content.content.substring(0, 150)}...
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {formatDate(content.createdAt)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline">
                          {content.type}
                        </Badge>
                        <div className="flex space-x-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => removeContent(content.id)}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto text-muted-foreground opacity-50 mb-4" />
                  <h3 className="text-lg font-medium">No Content Found</h3>
                  <p className="text-muted-foreground">
                    {searchTerm || typeFilter !== 'all'
                      ? 'Try adjusting your filters or search terms'
                      : 'Your generated content will appear here once you create some'}
                  </p>
                </div>
              )
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}