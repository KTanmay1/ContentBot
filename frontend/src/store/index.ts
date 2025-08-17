import { create } from 'zustand'
import { apiClient } from '@/lib/api'

// Types
export interface WorkflowState {
  id: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled'
  progress: number
  result?: any
  error?: string
  createdAt: Date
  updatedAt: Date
}

export interface ContentItem {
  id: string
  type: 'blog' | 'social'
  title: string
  content: string
  metadata: any
  createdAt: Date
  updatedAt: Date
}

export interface SystemStatus {
  database: 'healthy' | 'unhealthy'
  llm_provider: 'healthy' | 'unhealthy'
  agents: Record<string, 'healthy' | 'unhealthy'>
  lastChecked: Date
}

// Main Store Interface
interface AppStore {
  // UI State
  sidebarOpen: boolean
  currentPage: string
  loading: boolean
  error: string | null
  
  // Workflow State
  workflows: WorkflowState[]
  activeWorkflow: WorkflowState | null
  
  // Content State
  contents: ContentItem[]
  selectedContent: ContentItem | null
  
  // System State
  systemStatus: SystemStatus | null
  
  // Actions
  setSidebarOpen: (open: boolean) => void
  setCurrentPage: (page: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  addWorkflow: (workflow: WorkflowState) => void
  updateWorkflow: (id: string, updates: Partial<WorkflowState>) => void
  removeWorkflow: (id: string) => void
  setActiveWorkflow: (workflow: WorkflowState | null) => void
  addContent: (content: ContentItem) => void
  updateContent: (id: string, updates: Partial<ContentItem>) => void
  removeContent: (id: string) => void
  setSelectedContent: (content: ContentItem | null) => void
  loadContents: () => Promise<void>
  updateSystemStatus: (status: SystemStatus) => void
  checkSystemHealth: () => Promise<void>
  createWorkflow: (type: string, inputData: any) => Promise<string>
  pollWorkflowStatus: (workflowId: string) => Promise<void>
  pauseWorkflow: (workflowId: string) => Promise<void>
  resumeWorkflow: (workflowId: string) => Promise<void>
  cancelWorkflow: (workflowId: string) => Promise<void>
}

// Create the store
export const useAppStore = create<AppStore>((set, get) => ({
  // Initial State
  sidebarOpen: true,
  currentPage: 'home',
  loading: false,
  error: null,
  workflows: [],
  activeWorkflow: null,
  contents: [],
  selectedContent: null,
  systemStatus: null,
  
  // Actions
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  setCurrentPage: (page: string) => set({ currentPage: page }),
  setLoading: (loading: boolean) => set({ loading }),
  setError: (error: string | null) => set({ error }),
  
  addWorkflow: (workflow: WorkflowState) => 
    set((state) => ({ workflows: [...state.workflows, workflow] })),
  
  updateWorkflow: (id: string, updates: Partial<WorkflowState>) => 
    set((state) => ({
      workflows: state.workflows.map((w) => 
        w.id === id ? { ...w, ...updates, updatedAt: new Date() } : w
      ),
      activeWorkflow: state.activeWorkflow?.id === id 
        ? { ...state.activeWorkflow, ...updates, updatedAt: new Date() }
        : state.activeWorkflow
    })),
  
  removeWorkflow: (id: string) => 
    set((state) => ({
      workflows: state.workflows.filter((w) => w.id !== id),
      activeWorkflow: state.activeWorkflow?.id === id ? null : state.activeWorkflow
    })),
  
  setActiveWorkflow: (workflow: WorkflowState | null) => set({ activeWorkflow: workflow }),
  
  addContent: (content: ContentItem) => 
    set((state) => ({ contents: [content, ...state.contents] })),
  
  updateContent: (id: string, updates: Partial<ContentItem>) => 
    set((state) => ({
      contents: state.contents.map((c) => 
        c.id === id ? { ...c, ...updates, updatedAt: new Date() } : c
      ),
      selectedContent: state.selectedContent?.id === id 
        ? { ...state.selectedContent, ...updates, updatedAt: new Date() }
        : state.selectedContent
    })),
  
  removeContent: (id: string) => 
    set((state) => ({
      contents: state.contents.filter((c) => c.id !== id),
      selectedContent: state.selectedContent?.id === id ? null : state.selectedContent
    })),
  
  setSelectedContent: (content: ContentItem | null) => set({ selectedContent: content }),
  
  loadContents: async () => {
    try {
      set({ loading: true, error: null })
      const response = await apiClient.listContent({ limit: 50 })
      set({ contents: response.items || [] })
    } catch (error: any) {
      set({ error: error.message || 'Failed to load contents' })
    } finally {
      set({ loading: false })
    }
  },
  
  updateSystemStatus: (status: SystemStatus) => set({ systemStatus: status }),
  
  checkSystemHealth: async () => {
    try {
      const [systemStatus, agentStatus] = await Promise.all([
        apiClient.getSystemStatus(),
        apiClient.getAgentStatus()
      ])
      
      set({
        systemStatus: {
          database: systemStatus.database?.status || 'unhealthy',
          llm_provider: systemStatus.llm_provider?.status || 'unhealthy',
          agents: agentStatus.agents || {},
          lastChecked: new Date()
        }
      })
    } catch (error: any) {
      set({ error: error.message || 'Failed to check system health' })
    }
  },
  
  createWorkflow: async (type: string, inputData: any) => {
    try {
      set({ loading: true, error: null })
      const response = await apiClient.createWorkflow({
        workflow_type: type,
        input_data: inputData
      })
      
      const workflow: WorkflowState = {
        id: response.workflow_id,
        type,
        status: 'pending',
        progress: 0,
        createdAt: new Date(),
        updatedAt: new Date()
      }
      
      get().addWorkflow(workflow)
      get().setActiveWorkflow(workflow)
      
      return response.workflow_id
    } catch (error: any) {
      set({ error: error.message || 'Failed to create workflow' })
      throw error
    } finally {
      set({ loading: false })
    }
  },
  
  pollWorkflowStatus: async (workflowId: string) => {
    try {
      const status = await apiClient.getWorkflowStatus(workflowId)
      get().updateWorkflow(workflowId, {
        status: status.status,
        progress: status.progress || 0,
        error: status.error
      })
      
      if (status.status === 'completed') {
        const result = await apiClient.getWorkflowResult(workflowId)
        get().updateWorkflow(workflowId, { result: result.content })
      }
    } catch (error: any) {
      get().updateWorkflow(workflowId, {
        status: 'failed',
        error: error.message || 'Failed to get workflow status'
      })
    }
  },
  
  pauseWorkflow: async (workflowId: string) => {
    try {
      await apiClient.pauseWorkflow(workflowId)
      get().updateWorkflow(workflowId, { status: 'paused' })
    } catch (error: any) {
      set({ error: error.message || 'Failed to pause workflow' })
    }
  },
  
  resumeWorkflow: async (workflowId: string) => {
    try {
      await apiClient.resumeWorkflow(workflowId)
      get().updateWorkflow(workflowId, { status: 'running' })
    } catch (error: any) {
      set({ error: error.message || 'Failed to resume workflow' })
    }
  },
  
  cancelWorkflow: async (workflowId: string) => {
    try {
      await apiClient.cancelWorkflow(workflowId)
      get().updateWorkflow(workflowId, { status: 'cancelled' })
    } catch (error: any) {
      set({ error: error.message || 'Failed to cancel workflow' })
    }
  }
}))

// Utility hooks
export const useWorkflows = () => useAppStore((state) => state.workflows)
export const useActiveWorkflow = () => useAppStore((state) => state.activeWorkflow)
export const useContents = () => useAppStore((state) => state.contents)
export const useSystemStatus = () => useAppStore((state) => state.systemStatus)
export const useLoading = () => useAppStore((state) => state.loading)
export const useError = () => useAppStore((state) => state.error)