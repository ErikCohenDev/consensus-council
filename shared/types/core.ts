/**
 * Core type definitions shared between backend and frontend
 *
 * These types ensure end-to-end type safety across the entire system.
 * All API contracts, data models, and business logic types are defined here.
 */

// Base types
export type UUID = string;
export type Timestamp = number;
export type ModelProvider = 'openai' | 'anthropic' | 'google' | 'openrouter';
export type DocumentStage = 'research_brief' | 'market_scan' | 'vision' | 'prd' | 'architecture' | 'implementation_plan';
export type AuditStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
export type DebateStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type NotificationPriority = 1 | 2 | 3 | 4; // low | medium | high | critical

// Document-related types
export interface DocumentInfo {
  readonly name: string;
  readonly stage: DocumentStage;
  readonly exists: boolean;
  readonly wordCount: number;
  readonly lastModified: Timestamp | null;
  readonly auditStatus: AuditStatus;
  readonly consensusScore: number | null;
  readonly alignmentIssues: number;
}

export interface DocumentContent {
  readonly stage: DocumentStage;
  readonly content: string;
  readonly metadata: Record<string, unknown>;
}

// Audit-related types
export interface AuditorResponse {
  readonly auditorRole: string;
  readonly modelProvider: ModelProvider;
  readonly overallAssessment: {
    readonly summary: string;
    readonly topRisks: string[];
    readonly quickWins: string[];
    readonly overallPass: boolean;
  };
  readonly scoresDetailed: Record<string, {
    readonly score: number;
    readonly pass: boolean;
    readonly justification: string;
    readonly improvements: string[];
  }>;
  readonly blockingIssues: string[];
  readonly confidenceLevel: number;
}

export interface AuditRequest {
  readonly stage: DocumentStage;
  readonly content: string;
  readonly requesterId: string;
  readonly priority: number;
  readonly metadata?: Record<string, unknown>;
}

export interface AuditResult {
  readonly requestId: string;
  readonly stage: DocumentStage;
  readonly success: boolean;
  readonly auditorResponses: AuditorResponse[];
  readonly consensusResult: ConsensusResult | null;
  readonly executionTime: number;
  readonly costEstimate: number;
  readonly errorMessage?: string;
}

export interface ConsensusResult {
  readonly finalDecision: 'PASS' | 'FAIL';
  readonly weightedAverage: number;
  readonly agreementLevel: number;
  readonly individualScores: number[];
  readonly approvalCount: number;
  readonly criticalIssues: string[];
}

// Council and debate types
export interface CouncilMemberInfo {
  readonly memberId: string;
  readonly role: string;
  readonly provider: ModelProvider;
  readonly model: string;
  readonly expertiseAreas: string[];
  readonly personality: string;
  readonly debateStyle: string;
  readonly currentStatus: 'idle' | 'reviewing' | 'responding' | 'debating' | 'questioning';
  readonly insightsContributed: number;
  readonly agreementsMade: number;
  readonly questionsAsked: number;
}

export interface DebateRound {
  readonly roundNumber: number;
  readonly participants: string[];
  readonly initialReviews: Record<string, Record<string, unknown>>;
  readonly peerResponses: Record<string, Record<string, unknown>>;
  readonly emergingConsensus: string[];
  readonly disagreements: string[];
  readonly questionsRaised: string[];
  readonly durationSeconds: number;
  readonly status: DebateStatus;
}

export interface DebateSession {
  readonly sessionId: string;
  readonly documentStage: DocumentStage;
  readonly participants: CouncilMemberInfo[];
  readonly rounds: DebateRound[];
  readonly finalConsensus: string[];
  readonly unresolvedIssues: string[];
  readonly consensusScore: number;
  readonly totalDuration: number;
  readonly status: DebateStatus;
  readonly createdAt: Timestamp;
  readonly completedAt: Timestamp | null;
}

// Research and context types
export interface ResearchProgress {
  readonly stage: DocumentStage;
  readonly queriesExecuted: string[];
  readonly sourcesFound: number;
  readonly contextAdded: boolean;
  readonly durationSeconds: number;
  readonly status: 'searching' | 'processing' | 'completed' | 'failed';
}

export interface ResearchSource {
  readonly url: string;
  readonly title: string;
  readonly snippet: string;
  readonly relevanceScore: number;
  readonly publishedAt: Timestamp | null;
}

// Pipeline and orchestration types
export interface PipelineProgress {
  readonly documents: DocumentInfo[];
  readonly councilMembers: CouncilMemberInfo[];
  readonly currentDebateRound: DebateRound | null;
  readonly researchProgress: ResearchProgress[];
  readonly totalCostUsd: number;
  readonly executionTime: number;
  readonly overallStatus: 'idle' | 'initializing' | 'running' | 'completed' | 'failed';
}

export interface PipelineConfiguration {
  readonly docsPath: string;
  readonly stage?: DocumentStage;
  readonly model: string;
  readonly maxParallel: number;
  readonly timeoutSeconds: number;
  readonly enableCache: boolean;
  readonly interactive: boolean;
}

// Notification and real-time types
export interface NotificationMessage {
  readonly type: 'status_update' | 'audit_started' | 'audit_completed' | 'debate_started' | 'debate_round_completed' | 'consensus_reached' | 'error_occurred' | 'system_alert';
  readonly data: Record<string, unknown>;
  readonly timestamp: Timestamp;
  readonly priority: NotificationPriority;
}

export interface WebSocketMessage {
  readonly type: string;
  readonly data: Record<string, unknown>;
  readonly timestamp: Timestamp;
}

// API request/response types
export interface ApiResponse<T = unknown> {
  readonly success: boolean;
  readonly data?: T;
  readonly error?: string;
  readonly timestamp: Timestamp;
}

export interface StartAuditRequest {
  readonly docsPath: string;
  readonly stage?: DocumentStage;
  readonly model?: string;
}

export interface GetStatusResponse {
  readonly pipeline: PipelineProgress;
  readonly metrics: {
    readonly totalAudits: number;
    readonly totalCost: number;
    readonly avgDuration: number;
    readonly successRate: number;
  };
}

// Configuration and settings types
export interface UIConfiguration {
  readonly host: string;
  readonly port: number;
  readonly docsPath: string;
  readonly projectId: string;
  readonly autoRefresh: boolean;
  readonly debug: boolean;
  readonly theme: 'light' | 'dark' | 'auto';
}

export interface ModelConfiguration {
  readonly provider: ModelProvider;
  readonly model: string;
  readonly apiKey: string;
  readonly role: string;
  readonly maxTokens?: number;
  readonly temperature?: number;
}

// Utility types for better type safety
export type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;
export type NonEmptyArray<T> = [T, ...T[]];

// Event types for the event system
export interface SystemEvent {
  readonly type: string;
  readonly data: Record<string, unknown>;
  readonly timestamp: Timestamp;
  readonly source: string;
}

export interface AuditEvent extends SystemEvent {
  readonly type: 'audit_started' | 'audit_completed' | 'audit_failed';
  readonly data: {
    readonly requestId: string;
    readonly stage: DocumentStage;
    readonly success?: boolean;
    readonly error?: string;
  };
}

export interface DebateEvent extends SystemEvent {
  readonly type: 'debate_started' | 'debate_round_completed' | 'debate_completed' | 'debate_failed';
  readonly data: {
    readonly sessionId: string;
    readonly roundNumber?: number;
    readonly participants?: string[];
    readonly consensusScore?: number;
  };
}

// Error types for better error handling
export interface AppError {
  readonly code: string;
  readonly message: string;
  readonly details?: Record<string, unknown>;
  readonly timestamp: Timestamp;
  readonly stack?: string;
}

export type ValidationError = AppError & {
  readonly code: 'VALIDATION_ERROR';
  readonly field: string;
  readonly value: unknown;
};

export type NetworkError = AppError & {
  readonly code: 'NETWORK_ERROR';
  readonly statusCode: number;
  readonly method: string;
  readonly url: string;
};

// Metric and monitoring types
export interface PerformanceMetrics {
  readonly totalRequests: number;
  readonly successfulRequests: number;
  readonly failedRequests: number;
  readonly averageResponseTime: number;
  readonly totalCost: number;
  readonly cacheHitRate: number;
}

export interface SystemHealth {
  readonly status: 'healthy' | 'degraded' | 'unhealthy';
  readonly version: string;
  readonly uptime: number;
  readonly connections: number;
  readonly memory: {
    readonly used: number;
    readonly total: number;
  };
  readonly lastCheck: Timestamp;
}

// Export all types as a namespace for easier imports
export namespace LLMCouncil {
  export type {
    UUID,
    Timestamp,
    ModelProvider,
    DocumentStage,
    AuditStatus,
    DebateStatus,
    NotificationPriority,
    DocumentInfo,
    DocumentContent,
    AuditorResponse,
    AuditRequest,
    AuditResult,
    ConsensusResult,
    CouncilMemberInfo,
    DebateRound,
    DebateSession,
    ResearchProgress,
    ResearchSource,
    PipelineProgress,
    PipelineConfiguration,
    NotificationMessage,
    WebSocketMessage,
    ApiResponse,
    StartAuditRequest,
    GetStatusResponse,
    UIConfiguration,
    ModelConfiguration,
    SystemEvent,
    AuditEvent,
    DebateEvent,
    AppError,
    ValidationError,
    NetworkError,
    PerformanceMetrics,
    SystemHealth
  }
}
