import { useEffect, useMemo, useState } from 'react'
import { useId } from 'react'

type ContextQuestion = {
  id: string
  category: string
  text: string
  weight: number
  answer?: string
}

type SavedIdea = {
  id: string
  title: string
  text: string
  questions: ContextQuestion[]
  score: number
  updatedAt: number
}

const LS_KEY = 'llm-council.context-ideas'

const baseQuestionTemplates: Omit<ContextQuestion, 'id'>[] = [
  { category: 'Problem', text: 'What specific problem are you solving? For whom?', weight: 2 },
  { category: 'Audience', text: 'Who is the primary target user/customer? Describe personas.', weight: 2 },
  { category: 'Value', text: 'What is the core value proposition in one sentence?', weight: 2 },
  { category: 'Differentiation', text: 'How is this different from existing alternatives?', weight: 1.5 },
  { category: 'Market', text: 'Which market segment(s) and size are you targeting?', weight: 1.5 },
  { category: 'Distribution', text: 'How will users discover and adopt this? Channels?', weight: 1.5 },
  { category: 'Metrics', text: 'What are the success metrics (e.g., DAU, retention, revenue)?', weight: 2 },
  { category: 'Constraints', text: 'List constraints (budget, time, data availability, compliance).', weight: 1.5 },
  { category: 'Risks', text: 'Top 3 risks and your mitigation ideas.', weight: 1.5 },
  { category: 'Feasibility', text: 'Any technical feasibility or data requirements to note?', weight: 1.5 },
  { category: 'Security/Privacy', text: 'Any privacy/security or regulatory concerns (e.g., HIPAA, GDPR)?', weight: 1.2 },
  { category: 'Timeline', text: 'What is the milestone timeline (MVP, Beta, GA)?', weight: 1.2 },
  { category: 'Budget', text: 'Approximate budget and resource assumptions.', weight: 1.2 },
]

const generateId = () => Math.random().toString(36).slice(2)

const generateProjectTitle = (text: string) => {
  const words = text.trim().split(/\s+/).slice(0, 3)
  return words.map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') || 'Untitled Idea'
}

const qualityFactor = (q: ContextQuestion): number => {
  const a = (q.answer || '').trim()
  if (!a) return 0
  // Reward substantive answers ~2-3 sentences (~120 chars)
  const lenFactor = Math.min(1, a.length / 120)
  // Bonus if includes numbers for metrics/budget/timeline
  const needsNumbers = ['Metrics', 'Budget', 'Timeline']
  const numBonus = needsNumbers.includes(q.category) && /\d/.test(a) ? 0.15 : 0
  return Math.min(1, lenFactor + numBonus)
}

const computeScore = (questions: ContextQuestion[]): number => {
  if (questions.length === 0) return 0
  const totalWeight = questions.reduce((s, q) => s + q.weight, 0)
  const earned = questions.reduce((s, q) => s + q.weight * qualityFactor(q), 0)
  return Math.round((earned / Math.max(1e-6, totalWeight)) * 100)
}

export const ContextPage = () => {
  const ideaInputId = useId()
  const [ideaText, setIdeaText] = useState('')
  const [questions, setQuestions] = useState<ContextQuestion[]>([])
  const [savedIdeas, setSavedIdeas] = useState<SavedIdea[]>([])

  // Load/save from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY)
      if (raw) setSavedIdeas(JSON.parse(raw))
    } catch (_) {}
  }, [])

  const score = useMemo(() => computeScore(questions), [questions])

  const generateQuestions = () => {
    const idPrefix = generateId()
    const qs: ContextQuestion[] = baseQuestionTemplates.map((t, i) => ({
      id: `${idPrefix}-${i}`,
      category: t.category,
      text: t.text,
      weight: t.weight,
      answer: questions[i]?.answer || '',
    }))

    // Light tailoring from keywords in idea
    const txt = ideaText.toLowerCase()
    if (txt.includes('health') || txt.includes('medical')) {
      qs.push({
        id: `${idPrefix}-health`,
        category: 'Compliance',
        text: 'Does this handle PHI/PII? Outline HIPAA/PHI handling and safeguards.',
        weight: 1.2,
      })
    }
    if (txt.includes('ai') || txt.includes('model')) {
      qs.push({
        id: `${idPrefix}-ai`,
        category: 'Data',
        text: 'What data sources and labeling strategy will you use? Any licensing constraints?',
        weight: 1.2,
      })
    }
    setQuestions(qs)
  }

  const saveIdea = () => {
    const id = generateId()
    const title = generateProjectTitle(ideaText)
    const idea: SavedIdea = {
      id,
      title,
      text: ideaText,
      questions: questions,
      score: computeScore(questions),
      updatedAt: Date.now(),
    }
    const updated = [idea, ...savedIdeas].sort((a, b) => b.score - a.score).slice(0, 50)
    setSavedIdeas(updated)
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(updated))
    } catch (_) {}
  }

  const loadIdea = (id: string) => {
    const found = savedIdeas.find((i) => i.id === id)
    if (!found) return
    setIdeaText(found.text)
    setQuestions(found.questions)
  }

  const sortedSaved = useMemo(() => savedIdeas.slice().sort((a, b) => b.score - a.score), [savedIdeas])

  return (
    <div className="h-full flex">
      {/* Main editor */}
      <div className="flex-1 flex flex-col">
        <div className="border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-6 py-4">
          <h1 className="text-xl font-semibold">Context Builder</h1>
          <p className="text-sm opacity-70">Capture key context to improve council outputs</p>
        </div>

        <div className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-3">
            <div>
              <div className="text-sm font-medium mb-1">Idea</div>
              <textarea
                id={ideaInputId}
                value={ideaText}
                onChange={(e) => setIdeaText(e.target.value)}
                placeholder="Describe your idea in a few sentences..."
                className="w-full border rounded p-3 h-36 bg-white dark:bg-gray-800"
              />
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  className="px-3 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
                  onClick={generateQuestions}
                  disabled={!ideaText.trim()}
                >
                  Generate Questions
                </button>
                <button
                  type="button"
                  className="px-3 py-2 text-sm rounded bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
                  onClick={saveIdea}
                  disabled={questions.length === 0}
                >
                  Save Idea
                </button>
              </div>
            </div>

            <div className="border rounded p-3 bg-white dark:bg-gray-800">
              <div className="text-sm font-semibold mb-2">Context Score</div>
              <div className="text-3xl font-bold">{score}</div>
              <div className="text-xs opacity-70 mt-1">Higher scores indicate richer, more actionable context.</div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-4">
            {questions.length === 0 ? (
              <div className="border rounded p-6 text-sm opacity-70 bg-white dark:bg-gray-800">
                Add your idea and click Generate Questions to begin.
              </div>
            ) : (
              <div className="space-y-4">
                {questions.map((q, i) => (
                  <div key={q.id} className="border rounded p-3 bg-white dark:bg-gray-800">
                    <div className="text-xs opacity-70 mb-1">{q.category}</div>
                    <div className="text-sm font-medium mb-2">{i + 1}. {q.text}</div>
                    <textarea
                      value={q.answer || ''}
                      onChange={(e) => {
                        const val = e.target.value
                        setQuestions((prev) => prev.map((p) => (p.id === q.id ? { ...p, answer: val } : p)))
                      }}
                      placeholder="Your answer..."
                      className="w-full border rounded p-2 h-24 bg-white dark:bg-gray-700"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ranking sidebar */}
      <div className="w-80 border-l dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="font-semibold mb-2">Idea Ranking</div>
        <div className="text-xs opacity-70 mb-3">Sorted by context completeness.</div>

        {sortedSaved.length === 0 ? (
          <div className="text-sm opacity-70">No saved ideas yet.</div>
        ) : (
          <div className="space-y-2">
            {sortedSaved.map((item) => (
              <button
                key={item.id}
                onClick={() => loadIdea(item.id)}
                className="w-full text-left border rounded p-2 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium truncate max-w-[12rem]">{item.title}</div>
                  <div className="text-sm font-semibold">{item.score}</div>
                </div>
                <div className="text-xs opacity-70 truncate">{item.text}</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

