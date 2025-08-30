import type { CouncilMemberInfo, NotificationMessage } from '@shared/types/core'
import { useEffect } from 'react'
import { getWebSocketService } from '@/services/websocketService'
import { useAppActions, useAppStore } from '@/stores/appStore'

// import { Schemas, parseWithSchema } from '@shared/schemas/validation'

const mapActivityToStatus = (activity: unknown): CouncilMemberInfo['currentStatus'] => {
	switch (activity) {
		case 'reviewing':
		case 'responding':
		case 'debating':
		case 'questioning':
			return activity
		default:
			return 'idle'
	}
}

const mapProvider = (p: unknown): CouncilMemberInfo['provider'] => {
	if (p === 'openai' || p === 'anthropic' || p === 'google' || p === 'openrouter') return p
	return 'openai'
}

const mapCouncilMembers = (rawMembers: unknown): CouncilMemberInfo[] => {
	if (!Array.isArray(rawMembers)) return []
	return rawMembers.map((m: any) => ({
		memberId: String(
			m.role ?? crypto.randomUUID?.() ?? `member_${Math.random().toString(36).slice(2, 8)}`
		),
		role: String(m.role ?? 'member'),
		provider: mapProvider(m.model_provider),
		model: String(m.model_name ?? 'unknown'),
		expertiseAreas: Array.isArray(m.expertiseAreas) ? m.expertiseAreas : [],
		personality: String(m.personality ?? 'balanced'),
		debateStyle: String(m.debateStyle ?? 'analytic'),
		currentStatus: mapActivityToStatus(m.current_activity),
		insightsContributed: Number(m.insights_contributed ?? 0),
		agreementsMade: Number(m.agreements_made ?? 0),
		questionsAsked: Number(m.questions_asked ?? 0),
	}))
}

export const useWebSocketConnection = () => {
	const {
		setConnectionStatus,
		updateHeartbeat,
		setPipelineProgress,
		setAuditRunning,
		setCouncilMembers,
		addNotification,
		setError,
		incrementErrorCount,
	} = useAppActions()
	const config = useAppStore((s) => s.configuration)

	useEffect(() => {
				const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws?projectId=${encodeURIComponent(
			config.projectId || 'local'
		)}`
		const ws = getWebSocketService({ url: wsUrl })

		const offConn = ws.onConnection((connected) => {
			setConnectionStatus(connected ? 'connected' : 'disconnected')
			if (connected) updateHeartbeat()
		})

		const offErr = ws.onError((err) => {
			setConnectionStatus('error')
			setError(err.message)
			incrementErrorCount()
		})

		const offMsg = ws.onMessage((message: NotificationMessage) => {
			try {
				// Always record notifications
				addNotification(message)
				updateHeartbeat()

				switch (message.type) {
					case 'status_update': {
						// Try to parse pipeline status if present
						const candidate = (message.data as any) ?? {}
						if (candidate && typeof candidate === 'object' && 'documents' in candidate) {
							const pipeline = transformPipeline(candidate)
							setPipelineProgress(pipeline)
						}
						// Also update members when included from council_initialized mapping
						if ('members' in candidate) {
							const members = mapCouncilMembers((candidate as any).members)
							if (members.length) setCouncilMembers(members)
						}
						break
					}
					case 'audit_started': {
						setAuditRunning(true)
						break
					}
					case 'audit_completed': {
						setAuditRunning(false)
						const candidate = (message.data as any) ?? {}
						if (candidate && typeof candidate === 'object' && 'documents' in candidate) {
							const pipeline = transformPipeline(candidate)
							setPipelineProgress(pipeline)
						}
						break
					}
					case 'error_occurred': {
						const errMessage = String((message.data as any)?.message ?? 'An error occurred')
						setError(errMessage)
						incrementErrorCount()
						break
					}
					default:
						// system_alert or other types: no-op for now
						break
				}
			} catch (e) {
				setError(e instanceof Error ? e.message : String(e))
				incrementErrorCount()
			}
		})

		return () => {
			offConn()
			offErr()
			offMsg()
		}
	}, [
		setConnectionStatus,
		updateHeartbeat,
		setPipelineProgress,
		setAuditRunning,
		setCouncilMembers,
		addNotification,
		setError,
		incrementErrorCount,
		config.projectId,
	])
}

// Helpers to convert backend snake_case payloads into shared camelCase types
const transformPipeline = (raw: any) => {
	const toTs = (dt: any): number | null => {
		if (!dt) return null
		const t = typeof dt === 'number' ? dt : Date.parse(String(dt))
		return Number.isFinite(t) ? t : null
	}

	const documents = Array.isArray(raw.documents)
		? raw.documents.map((d: any) => ({
				name: String(d.name ?? ''),
				stage: String(d.stage ?? 'research_brief'),
				exists: Boolean(d.exists ?? false),
				wordCount: Number(d.word_count ?? 0),
				lastModified: toTs(d.last_modified),
				auditStatus: String(d.audit_status ?? 'pending') as any,
				consensusScore: d.consensus_score == null ? null : Number(d.consensus_score),
				alignmentIssues: Number(d.alignment_issues ?? 0),
			}))
		: []

	const researchProgress = Array.isArray(raw.research_progress)
		? raw.research_progress.map((r: any) => ({
				stage: String(r.stage ?? 'research_brief'),
				queriesExecuted: Array.isArray(r.queries_executed) ? r.queries_executed.map(String) : [],
				sourcesFound: Number(r.sources_found ?? 0),
				contextAdded: Boolean(r.context_added ?? false),
				durationSeconds: Number(r.duration_seconds ?? 0),
				status: String(r.status ?? 'completed'),
			}))
		: []

	const currentDebateRound = raw.current_debate_round
		? {
				roundNumber: Number(raw.current_debate_round.round_number ?? 1),
				participants: Array.isArray(raw.current_debate_round.participants)
					? raw.current_debate_round.participants.map(String)
					: [],
				initialReviews: {},
				peerResponses: {},
				emergingConsensus: Array.isArray(raw.current_debate_round.consensus_points)
					? raw.current_debate_round.consensus_points.map(String)
					: [],
				disagreements: Array.isArray(raw.current_debate_round.disagreements)
					? raw.current_debate_round.disagreements.map(String)
					: [],
				questionsRaised: Array.isArray(raw.current_debate_round.questions_raised)
					? raw.current_debate_round.questions_raised.map(String)
					: [],
				durationSeconds: Number(raw.current_debate_round.duration_seconds ?? 0),
				status: String(raw.current_debate_round.status ?? 'completed') as any,
			}
		: null

	return {
		documents,
		councilMembers: Array.isArray(raw.council_members)
			? mapCouncilMembers(raw.council_members)
			: [],
		currentDebateRound,
		researchProgress,
		totalCostUsd: Number(raw.total_cost_usd ?? 0),
		executionTime: Number(raw.execution_time ?? 0),
		overallStatus: String(raw.overall_status ?? 'idle') as any,
	}
}
