/**
 * Zod schemas for runtime validation
 * 
 * These schemas provide runtime type checking and validation for all data
 * flowing between the frontend and backend. They ensure type safety at runtime
 * and provide excellent error messages for debugging.
 */

import { z } from 'zod'

// Base schemas
export const UUIDSchema = z.string().uuid()
export const TimestampSchema = z.number().int().nonnegative()
export const ModelProviderSchema = z.enum(['openai', 'anthropic', 'google', 'openrouter'])
export const DocumentStageSchema = z.enum([
  'research_brief',
  'market_scan', 
  'vision',
  'prd',
  'architecture',
  'implementation_plan'
])
export const AuditStatusSchema = z.enum(['pending', 'in_progress', 'completed', 'failed', 'skipped'])
export const DebateStatusSchema = z.enum(['pending', 'in_progress', 'completed', 'failed', 'cancelled'])
export const NotificationPrioritySchema = z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4)])

// Document schemas
export const DocumentInfoSchema = z.object({
  name: z.string().min(1),
  stage: DocumentStageSchema,
  exists: z.boolean(),
  wordCount: z.number().int().nonnegative(),
  lastModified: TimestampSchema.nullable(),
  auditStatus: AuditStatusSchema,
  consensusScore: z.number().min(0).max(5).nullable(),
  alignmentIssues: z.number().int().nonnegative(),
}).readonly()

export const DocumentContentSchema = z.object({
  stage: DocumentStageSchema,
  content: z.string(),
  metadata: z.record(z.string(), z.unknown()),
}).readonly()

// Audit schemas
export const ScoreDetailSchema = z.object({
  score: z.number().min(0).max(5),
  pass: z.boolean(),
  justification: z.string().min(10),
  improvements: z.array(z.string()).min(1),
}).readonly()

export const OverallAssessmentSchema = z.object({
  summary: z.string().min(20),
  topRisks: z.array(z.string()).max(5),
  quickWins: z.array(z.string()).max(5),
  overallPass: z.boolean(),
}).readonly()

export const AuditorResponseSchema = z.object({
  auditorRole: z.string().min(1),
  modelProvider: ModelProviderSchema,
  overallAssessment: OverallAssessmentSchema,
  scoresDetailed: z.record(z.string(), ScoreDetailSchema),
  blockingIssues: z.array(z.string()),
  confidenceLevel: z.number().min(0).max(1),
}).readonly()

export const AuditRequestSchema = z.object({
  stage: DocumentStageSchema,
  content: z.string().min(1),
  requesterId: z.string().min(1),
  priority: z.number().int().min(1).max(10),
  metadata: z.record(z.string(), z.unknown()).optional(),
}).readonly()

export const ConsensusResultSchema = z.object({
  finalDecision: z.enum(['PASS', 'FAIL']),
  weightedAverage: z.number().min(0).max(5),
  agreementLevel: z.number().min(0).max(1),
  individualScores: z.array(z.number().min(0).max(5)),
  approvalCount: z.number().int().nonnegative(),
  criticalIssues: z.array(z.string()),
}).readonly()

export const AuditResultSchema = z.object({
  requestId: z.string().min(1),
  stage: DocumentStageSchema,
  success: z.boolean(),
  auditorResponses: z.array(AuditorResponseSchema),
  consensusResult: ConsensusResultSchema.nullable(),
  executionTime: z.number().nonnegative(),
  costEstimate: z.number().nonnegative(),
  errorMessage: z.string().optional(),
}).readonly()

// Council and debate schemas
export const CouncilMemberStatusSchema = z.enum(['idle', 'reviewing', 'responding', 'debating', 'questioning'])

export const CouncilMemberInfoSchema = z.object({
  memberId: z.string().min(1),
  role: z.string().min(1),
  provider: ModelProviderSchema,
  model: z.string().min(1),
  expertiseAreas: z.array(z.string()).min(1),
  personality: z.string().min(1),
  debateStyle: z.string().min(1),
  currentStatus: CouncilMemberStatusSchema,
  insightsContributed: z.number().int().nonnegative(),
  agreementsMade: z.number().int().nonnegative(),
  questionsAsked: z.number().int().nonnegative(),
}).readonly()

export const DebateRoundSchema = z.object({
  roundNumber: z.number().int().positive(),
  participants: z.array(z.string()).min(1),
  initialReviews: z.record(z.string(), z.record(z.string(), z.unknown())),
  peerResponses: z.record(z.string(), z.record(z.string(), z.unknown())),
  emergingConsensus: z.array(z.string()),
  disagreements: z.array(z.string()),
  questionsRaised: z.array(z.string()),
  durationSeconds: z.number().nonnegative(),
  status: DebateStatusSchema,
}).readonly()

export const DebateSessionSchema = z.object({
  sessionId: z.string().min(1),
  documentStage: DocumentStageSchema,
  participants: z.array(CouncilMemberInfoSchema),
  rounds: z.array(DebateRoundSchema),
  finalConsensus: z.array(z.string()),
  unresolvedIssues: z.array(z.string()),
  consensusScore: z.number().min(0).max(1),
  totalDuration: z.number().nonnegative(),
  status: DebateStatusSchema,
  createdAt: TimestampSchema,
  completedAt: TimestampSchema.nullable(),
}).readonly()

// Research schemas
export const ResearchProgressSchema = z.object({
  stage: DocumentStageSchema,
  queriesExecuted: z.array(z.string()),
  sourcesFound: z.number().int().nonnegative(),
  contextAdded: z.boolean(),
  durationSeconds: z.number().nonnegative(),
  status: z.enum(['searching', 'processing', 'completed', 'failed']),
}).readonly()

export const ResearchSourceSchema = z.object({
  url: z.string().url(),
  title: z.string().min(1),
  snippet: z.string(),
  relevanceScore: z.number().min(0).max(1),
  publishedAt: TimestampSchema.nullable(),
}).readonly()

// Pipeline schemas
export const PipelineProgressSchema = z.object({
  documents: z.array(DocumentInfoSchema),
  councilMembers: z.array(CouncilMemberInfoSchema),
  currentDebateRound: DebateRoundSchema.nullable(),
  researchProgress: z.array(ResearchProgressSchema),
  totalCostUsd: z.number().nonnegative(),
  executionTime: z.number().nonnegative(),
  overallStatus: z.enum(['idle', 'initializing', 'running', 'completed', 'failed']),
}).readonly()

export const PipelineConfigurationSchema = z.object({
  docsPath: z.string().min(1),
  stage: DocumentStageSchema.optional(),
  model: z.string().min(1),
  maxParallel: z.number().int().positive().max(20),
  timeoutSeconds: z.number().positive().max(600),
  enableCache: z.boolean(),
  interactive: z.boolean(),
}).readonly()

// Notification schemas
export const NotificationTypeSchema = z.enum([
  'status_update',
  'audit_started', 
  'audit_completed',
  'debate_started',
  'debate_round_completed',
  'consensus_reached',
  'error_occurred',
  'system_alert'
])

export const NotificationMessageSchema = z.object({
  type: NotificationTypeSchema,
  data: z.record(z.string(), z.unknown()),
  timestamp: TimestampSchema,
  priority: NotificationPrioritySchema,
}).readonly()

export const WebSocketMessageSchema = z.object({
  type: z.string().min(1),
  data: z.record(z.string(), z.unknown()),
  timestamp: TimestampSchema,
}).readonly()

// API schemas
export const ApiResponseSchema = <T extends z.ZodType>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z.string().optional(),
    timestamp: TimestampSchema,
  }).readonly()

export const StartAuditRequestSchema = z.object({
  docsPath: z.string().min(1),
  stage: DocumentStageSchema.optional(),
  model: z.string().min(1).optional(),
}).readonly()

export const GetStatusResponseSchema = z.object({
  pipeline: PipelineProgressSchema,
  metrics: z.object({
    totalAudits: z.number().int().nonnegative(),
    totalCost: z.number().nonnegative(),
    avgDuration: z.number().nonnegative(),
    successRate: z.number().min(0).max(1),
  }),
}).readonly()

// Configuration schemas
export const UIConfigurationSchema = z.object({
  host: z.string().min(1),
  port: z.number().int().positive().max(65535),
  docsPath: z.string().min(1),
  autoRefresh: z.boolean(),
  debug: z.boolean(),
  theme: z.enum(['light', 'dark', 'auto']),
}).readonly()

export const ModelConfigurationSchema = z.object({
  provider: ModelProviderSchema,
  model: z.string().min(1),
  apiKey: z.string().min(1),
  role: z.string().min(1),
  maxTokens: z.number().int().positive().optional(),
  temperature: z.number().min(0).max(2).optional(),
}).readonly()

// Error schemas
const AppErrorBaseSchema = z.object({
  code: z.string().min(1),
  message: z.string().min(1),
  details: z.record(z.string(), z.unknown()).optional(),
  timestamp: TimestampSchema,
  stack: z.string().optional(),
})

export const AppErrorSchema = AppErrorBaseSchema.readonly()

export const ValidationErrorSchema = AppErrorBaseSchema.extend({
  code: z.literal('VALIDATION_ERROR'),
  field: z.string().min(1),
  value: z.unknown(),
}).readonly()

export const NetworkErrorSchema = AppErrorBaseSchema.extend({
  code: z.literal('NETWORK_ERROR'),
  statusCode: z.number().int().min(100).max(599),
  method: z.string().min(1),
  url: z.string().url(),
}).readonly()

// System schemas
export const PerformanceMetricsSchema = z.object({
  totalRequests: z.number().int().nonnegative(),
  successfulRequests: z.number().int().nonnegative(),
  failedRequests: z.number().int().nonnegative(),
  averageResponseTime: z.number().nonnegative(),
  totalCost: z.number().nonnegative(),
  cacheHitRate: z.number().min(0).max(1),
}).readonly()

export const SystemHealthSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  version: z.string().min(1),
  uptime: z.number().nonnegative(),
  connections: z.number().int().nonnegative(),
  memory: z.object({
    used: z.number().nonnegative(),
    total: z.number().positive(),
  }),
  lastCheck: TimestampSchema,
}).readonly()

// Helper functions for validation
export const parseWithSchema = <T>(schema: z.ZodSchema<T>, data: unknown): T => {
  const result = schema.safeParse(data)
  if (!result.success) {
    throw new ValidationError(
      'VALIDATION_ERROR',
      `Validation failed: ${result.error.message}`,
      {
        errors: result.error.errors,
        input: data,
      }
    )
  }
  return result.data
}

export const validateApiResponse = <T>(
  dataSchema: z.ZodSchema<T>,
  response: unknown
): T => {
  const apiResponse = parseWithSchema(ApiResponseSchema(dataSchema), response)
  
  if (!apiResponse.success) {
    throw new Error(apiResponse.error || 'API request failed')
  }
  
  if (!apiResponse.data) {
    throw new Error('API response missing data')
  }
  
  return apiResponse.data
}

// Custom error classes
export class ValidationError extends Error {
  constructor(
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'ValidationError'
  }
}

// Export all schemas for easier importing
export const Schemas = {
  // Base
  UUID: UUIDSchema,
  Timestamp: TimestampSchema,
  ModelProvider: ModelProviderSchema,
  DocumentStage: DocumentStageSchema,
  AuditStatus: AuditStatusSchema,
  DebateStatus: DebateStatusSchema,
  NotificationPriority: NotificationPrioritySchema,
  
  // Document
  DocumentInfo: DocumentInfoSchema,
  DocumentContent: DocumentContentSchema,
  
  // Audit
  AuditorResponse: AuditorResponseSchema,
  AuditRequest: AuditRequestSchema,
  AuditResult: AuditResultSchema,
  ConsensusResult: ConsensusResultSchema,
  
  // Council
  CouncilMemberInfo: CouncilMemberInfoSchema,
  DebateRound: DebateRoundSchema,
  DebateSession: DebateSessionSchema,
  
  // Research
  ResearchProgress: ResearchProgressSchema,
  ResearchSource: ResearchSourceSchema,
  
  // Pipeline
  PipelineProgress: PipelineProgressSchema,
  PipelineConfiguration: PipelineConfigurationSchema,
  
  // Notifications
  NotificationMessage: NotificationMessageSchema,
  WebSocketMessage: WebSocketMessageSchema,
  
  // API
  StartAuditRequest: StartAuditRequestSchema,
  GetStatusResponse: GetStatusResponseSchema,
  
  // Configuration
  UIConfiguration: UIConfigurationSchema,
  ModelConfiguration: ModelConfigurationSchema,
  
  // Errors
  AppError: AppErrorSchema,
  ValidationError: ValidationErrorSchema,
  NetworkError: NetworkErrorSchema,
  
  // System
  PerformanceMetrics: PerformanceMetricsSchema,
  SystemHealth: SystemHealthSchema,
} as const