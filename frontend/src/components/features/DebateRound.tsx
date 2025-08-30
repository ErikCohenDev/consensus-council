import type React from 'react'

type DebateRoundProps = {
	roundNumber: number
	emergingConsensus: string[]
	disagreements: string[]
	questionsRaised?: string[]
	status?: string
}

export const DebateRound: React.FC<DebateRoundProps> = ({
	roundNumber,
	emergingConsensus,
	disagreements,
	questionsRaised = [],
	status,
}) => {
	return (
		<div aria-label={`debate-round-${roundNumber}`} className="border rounded p-3">
			<div className="font-medium mb-2">
				Debate Round {roundNumber}
				{status ? ` • ${status}` : ''}
			</div>
			<div className="grid grid-cols-2 gap-4">
				<div>
					<div className="text-sm font-semibold mb-1">
						Consensus Points ({emergingConsensus.length})
					</div>
					<ul className="text-sm list-disc pl-5">
						{emergingConsensus.map((c, i) => (
							<li key={i}>{c}</li>
						))}
					</ul>
				</div>
				<div>
					<div className="text-sm font-semibold mb-1">Disagreements ({disagreements.length})</div>
					<ul className="text-sm list-disc pl-5">
						{disagreements.map((d, i) => (
							<li key={i}>{d}</li>
						))}
					</ul>
				</div>
			</div>
			{questionsRaised.length > 0 && (
				<div className="mt-3">
					<div className="text-sm font-semibold mb-1">Questions Raised</div>
					<ul className="text-sm list-disc pl-5">
						{questionsRaised.map((q, i) => (
							<li key={i}>{q}</li>
						))}
					</ul>
				</div>
			)}
		</div>
	)
}
