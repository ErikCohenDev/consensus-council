/**
 * Main application store using Zustand
 * 
 * Manages global application state with proper TypeScript typing
 * and separation of concerns. Uses Zustand for its simplicity
 * and excellent TypeScript support.
 */

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { 
  PipelineProgress, 
  CouncilMemberInfo, 
  DebateSession,
  NotificationMessage,
  UIConfiguration 
} from '@shared/types/core'

interface AppState {
  // UI State
  theme: 'light' | 'dark' | 'auto'
  sidebarCollapsed: boolean
  currentPage: string
  
  // Connection State
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastHeartbeat: number | null
  
  // Pipeline State
  pipelineProgress: PipelineProgress | null
  isAuditRunning: boolean
  currentAuditStage: string | null
  
  // Council State
  councilMembers: CouncilMemberInfo[]
  activeDebateSession: DebateSession | null
  debateHistory: DebateSession[]
  
  // Notifications
  notifications: NotificationMessage[]
  unreadCount: number
  
  // Configuration
  configuration: Partial<UIConfiguration>
  
  // Error State
  lastError: string | null
  errorCount: number
}

interface AppActions {
  // UI Actions
  setTheme: (theme: 'light' | 'dark' | 'auto') => void
  toggleSidebar: () => void
  setCurrentPage: (page: string) => void
  
  // Connection Actions
  setConnectionStatus: (status: AppState['connectionStatus']) => void
  updateHeartbeat: () => void
  
  // Pipeline Actions
  setPipelineProgress: (progress: PipelineProgress) => void
  setAuditRunning: (running: boolean) => void
  setCurrentAuditStage: (stage: string | null) => void
  
  // Council Actions
  setCouncilMembers: (members: CouncilMemberInfo[]) => void
  updateCouncilMember: (memberId: string, updates: Partial<CouncilMemberInfo>) => void
  setActiveDebateSession: (session: DebateSession | null) => void
  addDebateToHistory: (session: DebateSession) => void
  
  // Notification Actions
  addNotification: (notification: NotificationMessage) => void
  removeNotification: (timestamp: number) => void
  clearNotifications: () => void
  markNotificationsRead: () => void
  
  // Configuration Actions
  updateConfiguration: (config: Partial<UIConfiguration>) => void
  
  // Error Actions
  setError: (error: string | null) => void
  incrementErrorCount: () => void
  clearErrors: () => void
  
  // Utility Actions
  reset: () => void
}

type AppStore = AppState & AppActions

const initialState: AppState = {
  // UI State
  theme: 'auto',
  sidebarCollapsed: false,
  currentPage: '/',
  
  // Connection State
  isConnected: false,
  connectionStatus: 'disconnected',
  lastHeartbeat: null,
  
  // Pipeline State
  pipelineProgress: null,
  isAuditRunning: false,
  currentAuditStage: null,
  
  // Council State
  councilMembers: [],
  activeDebateSession: null,
  debateHistory: [],
  
  // Notifications
  notifications: [],
  unreadCount: 0,
  
  // Configuration
  configuration: {
    host: 'localhost',
    port: 8000,
    docsPath: './docs',
    projectId: 'local',
    autoRefresh: true,
    debug: false,
    theme: 'auto',
  },
  
  // Error State
  lastError: null,
  errorCount: 0,
}

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,
        
        // UI Actions
        setTheme: (theme) => {
          set((state) => ({ ...state, theme }))
          
          // Update DOM class for theme
          const root = document.documentElement
          if (theme === 'dark') {
            root.classList.add('dark')
          } else if (theme === 'light') {
            root.classList.remove('dark')
          } else {
            // Auto theme - check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
            if (prefersDark) {
              root.classList.add('dark')
            } else {
              root.classList.remove('dark')
            }
          }
        },
        
        toggleSidebar: () =>
          set((state) => ({ ...state, sidebarCollapsed: !state.sidebarCollapsed })),
        
        setCurrentPage: (page) =>
          set((state) => ({ ...state, currentPage: page })),
        
        // Connection Actions
        setConnectionStatus: (connectionStatus) => {
          const isConnected = connectionStatus === 'connected'
          set((state) => ({ 
            ...state, 
            connectionStatus, 
            isConnected,
            lastHeartbeat: isConnected ? Date.now() : state.lastHeartbeat
          }))
        },
        
        updateHeartbeat: () =>
          set((state) => ({ ...state, lastHeartbeat: Date.now() })),
        
        // Pipeline Actions
        setPipelineProgress: (pipelineProgress) =>
          set((state) => ({ ...state, pipelineProgress })),
        
        setAuditRunning: (isAuditRunning) =>
          set((state) => ({ ...state, isAuditRunning })),
        
        setCurrentAuditStage: (currentAuditStage) =>
          set((state) => ({ ...state, currentAuditStage })),
        
        // Council Actions
        setCouncilMembers: (councilMembers) =>
          set((state) => ({ ...state, councilMembers })),
        
        updateCouncilMember: (memberId, updates) =>
          set((state) => ({
            ...state,
            councilMembers: state.councilMembers.map((member) =>
              member.memberId === memberId ? { ...member, ...updates } : member
            ),
          })),
        
        setActiveDebateSession: (activeDebateSession) =>
          set((state) => ({ ...state, activeDebateSession })),
        
        addDebateToHistory: (session) =>
          set((state) => ({
            ...state,
            debateHistory: [session, ...state.debateHistory.slice(0, 19)], // Keep last 20
          })),
        
        // Notification Actions
        addNotification: (notification) =>
          set((state) => ({
            ...state,
            notifications: [notification, ...state.notifications.slice(0, 99)], // Keep last 100
            unreadCount: state.unreadCount + 1,
          })),
        
        removeNotification: (timestamp) =>
          set((state) => ({
            ...state,
            notifications: state.notifications.filter((n) => n.timestamp !== timestamp),
          })),
        
        clearNotifications: () =>
          set((state) => ({ ...state, notifications: [], unreadCount: 0 })),
        
        markNotificationsRead: () =>
          set((state) => ({ ...state, unreadCount: 0 })),
        
        // Configuration Actions
        updateConfiguration: (config) =>
          set((state) => ({
            ...state,
            configuration: { ...state.configuration, ...config },
          })),
        
        // Error Actions
        setError: (lastError) =>
          set((state) => ({ ...state, lastError })),
        
        incrementErrorCount: () =>
          set((state) => ({ ...state, errorCount: state.errorCount + 1 })),
        
        clearErrors: () =>
          set((state) => ({ ...state, lastError: null, errorCount: 0 })),
        
        // Utility Actions
        reset: () => set(initialState),
      }),
      {
        name: 'llm-council-app-store',
        partialize: (state) => ({
          theme: state.theme,
          sidebarCollapsed: state.sidebarCollapsed,
          configuration: state.configuration,
          debateHistory: state.debateHistory.slice(0, 10), // Persist only recent history
        }),
      }
    ),
    {
      name: 'AppStore',
    }
  )
)

// Selectors for better performance
export const useConnectionState = () => 
  useAppStore((state) => ({
    isConnected: state.isConnected,
    connectionStatus: state.connectionStatus,
    lastHeartbeat: state.lastHeartbeat,
  }))

export const usePipelineState = () =>
  useAppStore((state) => ({
    pipelineProgress: state.pipelineProgress,
    isAuditRunning: state.isAuditRunning,
    currentAuditStage: state.currentAuditStage,
  }))

export const useCouncilState = () =>
  useAppStore((state) => ({
    councilMembers: state.councilMembers,
    activeDebateSession: state.activeDebateSession,
    debateHistory: state.debateHistory,
  }))

export const useNotificationState = () =>
  useAppStore((state) => ({
    notifications: state.notifications,
    unreadCount: state.unreadCount,
  }))

export const useUIState = () =>
  useAppStore((state) => ({
    theme: state.theme,
    sidebarCollapsed: state.sidebarCollapsed,
    currentPage: state.currentPage,
  }))

// Action selectors
export const useAppActions = () =>
  useAppStore((state) => ({
    setTheme: state.setTheme,
    toggleSidebar: state.toggleSidebar,
    setCurrentPage: state.setCurrentPage,
    setConnectionStatus: state.setConnectionStatus,
    updateHeartbeat: state.updateHeartbeat,
    setPipelineProgress: state.setPipelineProgress,
    setAuditRunning: state.setAuditRunning,
    setCurrentAuditStage: state.setCurrentAuditStage,
    setCouncilMembers: state.setCouncilMembers,
    updateCouncilMember: state.updateCouncilMember,
    setActiveDebateSession: state.setActiveDebateSession,
    addDebateToHistory: state.addDebateToHistory,
    addNotification: state.addNotification,
    removeNotification: state.removeNotification,
    clearNotifications: state.clearNotifications,
    markNotificationsRead: state.markNotificationsRead,
    updateConfiguration: state.updateConfiguration,
    setError: state.setError,
    incrementErrorCount: state.incrementErrorCount,
    clearErrors: state.clearErrors,
    reset: state.reset,
  }))
