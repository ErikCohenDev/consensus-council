import { render, screen } from '@testing-library/react'
import { DebateRound } from './DebateRound'

describe('DebateRound component', () => {
  it('renders round header and lists', () => {
    render(
      <DebateRound
        roundNumber={1}
        emergingConsensus={["Focus MVP", "Define metrics"]}
        disagreements={["Timeline too aggressive"]}
        questionsRaised={["What is the success metric?"]}
        status="completed"
      />
    )

    expect(screen.getByLabelText('debate-round-1')).toBeInTheDocument()
    expect(screen.getByText(/Debate Round 1/)).toBeInTheDocument()
    expect(screen.getByText('Consensus Points (2)')).toBeInTheDocument()
    expect(screen.getByText('Disagreements (1)')).toBeInTheDocument()
    expect(screen.getByText('What is the success metric?')).toBeInTheDocument()
  })
})
