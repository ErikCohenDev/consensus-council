/**
 * React UI for LLM Council Platform
 *
 * Provides real-time visualization of:
 * - Document pipeline progress
 * - Council member debates
 * - Research agent activities
 * - Consensus building and alignment validation
 */

const { useState, useEffect, useRef } = React;

// Status badge component
function StatusBadge({ status, text }) {
    const statusClasses = {
        pending: 'bg-yellow-100 text-yellow-800',
        'in-progress': 'bg-blue-100 text-blue-800',
        completed: 'bg-green-100 text-green-800',
        failed: 'bg-red-100 text-red-800',
        skipped: 'bg-gray-100 text-gray-600'
    };

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClasses[status] || 'bg-gray-100 text-gray-600'}`}>
            {text || status}
        </span>
    );
}

// Document card component
function DocumentCard({ document, onClick }) {
    const getStatusIcon = (status) => {
        switch (status) {
            case 'pending': return 'fa-clock';
            case 'in-progress': return 'fa-spinner fa-spin';
            case 'completed': return 'fa-check-circle';
            case 'failed': return 'fa-exclamation-circle';
            default: return 'fa-file';
        }
    };

    return (
        <div
            className={`bg-white rounded-lg shadow-sm border-2 p-4 cursor-pointer transition-all hover:shadow-md ${
                document.audit_status === 'in-progress' ? 'border-blue-300 bg-blue-50' :
                document.audit_status === 'completed' ? 'border-green-300' :
                'border-gray-200'
            }`}
            onClick={() => onClick(document)}
        >
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-900">{document.name}</h3>
                <i className={`fas ${getStatusIcon(document.audit_status)} ${
                    document.audit_status === 'completed' ? 'text-green-500' :
                    document.audit_status === 'in-progress' ? 'text-blue-500' :
                    document.audit_status === 'failed' ? 'text-red-500' :
                    'text-gray-400'
                }`}></i>
            </div>

            <div className="space-y-2">
                <StatusBadge status={document.audit_status} />

                <div className="text-xs text-gray-500 space-y-1">
                    <div>Stage: <span className="font-medium">{document.stage}</span></div>
                    <div>Words: <span className="font-medium">{document.word_count.toLocaleString()}</span></div>
                    {document.consensus_score && (
                        <div>Consensus: <span className="font-medium">{document.consensus_score.toFixed(2)}/5.0</span></div>
                    )}
                    {document.alignment_issues > 0 && (
                        <div className="text-red-500">
                            <i className="fas fa-exclamation-triangle"></i> {document.alignment_issues} alignment issues
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Council member card component
function CouncilMemberCard({ member }) {
    const getActivityIcon = (activity) => {
        switch (activity) {
            case 'reviewing': return 'fa-eye';
            case 'responding': return 'fa-comments';
            case 'debating': return 'fa-users';
            case 'questioning': return 'fa-question-circle';
            default: return 'fa-user';
        }
    };

    const getActivityColor = (activity) => {
        switch (activity) {
            case 'reviewing': return 'text-blue-500';
            case 'responding': return 'text-green-500';
            case 'debating': return 'text-orange-500';
            case 'questioning': return 'text-purple-500';
            default: return 'text-gray-400';
        }
    };

    return (
        <div className={`bg-white rounded-lg shadow-sm border p-4 ${
            member.current_activity === 'idle' ? '' : 'border-l-4 border-l-blue-500'
        }`}>
            <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-900 capitalize">{member.role}</h4>
                <i className={`fas ${getActivityIcon(member.current_activity)} ${getActivityColor(member.current_activity)}`}></i>
            </div>

            <div className="text-xs text-gray-500 space-y-1">
                <div>Provider: <span className="font-medium">{member.model_provider}</span></div>
                <div>Model: <span className="font-medium text-xs">{member.model_name.split('/').pop()}</span></div>
                <div>Activity: <span className="font-medium capitalize">{member.current_activity}</span></div>

                <div className="flex space-x-3 mt-2 text-xs">
                    <span>💡 {member.insights_contributed}</span>
                    <span>🤝 {member.agreements_made}</span>
                    <span>❓ {member.questions_asked}</span>
                </div>
            </div>
        </div>
    );
}

// Debate round visualization
function DebateRoundPanel({ debateRound }) {
    if (!debateRound) return null;

    return (
        <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">
                    Debate Round {debateRound.round_number}
                </h3>
                <StatusBadge status={debateRound.status} />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <h4 className="text-sm font-medium text-green-700 mb-2">
                        <i className="fas fa-handshake mr-1"></i>
                        Consensus Points ({debateRound.consensus_points.length})
                    </h4>
                    <ul className="space-y-1">
                        {debateRound.consensus_points.slice(0, 3).map((point, i) => (
                            <li key={i} className="text-xs text-green-600 bg-green-50 p-2 rounded">
                                {point}
                            </li>
                        ))}
                    </ul>
                </div>

                <div>
                    <h4 className="text-sm font-medium text-orange-700 mb-2">
                        <i className="fas fa-exclamation-triangle mr-1"></i>
                        Disagreements ({debateRound.disagreements.length})
                    </h4>
                    <ul className="space-y-1">
                        {debateRound.disagreements.slice(0, 3).map((disagreement, i) => (
                            <li key={i} className="text-xs text-orange-600 bg-orange-50 p-2 rounded">
                                {disagreement}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {debateRound.questions_raised.length > 0 && (
                <div className="mt-4">
                    <h4 className="text-sm font-medium text-purple-700 mb-2">
                        <i className="fas fa-question-circle mr-1"></i>
                        Questions Raised
                    </h4>
                    <div className="space-y-1">
                        {debateRound.questions_raised.slice(0, 2).map((question, i) => (
                            <div key={i} className="text-xs text-purple-600 bg-purple-50 p-2 rounded">
                                {question}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// Research progress panel
function ResearchProgressPanel({ researchProgress }) {
    if (!researchProgress.length) return null;

    return (
        <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-3">
                <i className="fas fa-search mr-2"></i>
                Research Progress
            </h3>

            <div className="space-y-3">
                {researchProgress.map((progress, i) => (
                    <div key={i} className="border-l-4 border-blue-300 pl-3">
                        <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium capitalize">{progress.stage}</span>
                            <StatusBadge status={progress.status} />
                        </div>

                        <div className="text-xs text-gray-600 space-y-1">
                            <div>Queries: {progress.queries_executed.join(', ').slice(0, 50)}...</div>
                            <div>Sources: {progress.sources_found}</div>
                            <div>Duration: {progress.duration_seconds.toFixed(1)}s</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Main application component
function LLMCouncilApp() {
    const [pipelineStatus, setPipelineStatus] = useState({
        documents: [],
        council_members: [],
        current_debate_round: null,
        research_progress: [],
        total_cost_usd: 0.0,
        execution_time: 0.0,
        overall_status: 'idle'
    });

    const [selectedDocument, setSelectedDocument] = useState(null);
    const [auditSettings, setAuditSettings] = useState({
        docs_path: './docs',
        stage: '',
        model: 'gpt-4o'
    });

    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState([]);
    const wsRef = useRef(null);

    // WebSocket connection for real-time updates
    useEffect(() => {
        const connectWebSocket = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            wsRef.current = new WebSocket(wsUrl);

            wsRef.current.onopen = () => {
                setIsConnected(true);
                console.log('WebSocket connected');
            };

            wsRef.current.onmessage = (event) => {
                const message = JSON.parse(event.data);
                console.log('WebSocket message:', message);

                switch (message.type) {
                    case 'status_update':
                        setPipelineStatus(message.status);
                        break;
                    case 'document_audit_started':
                        setPipelineStatus(prev => ({
                            ...prev,
                            documents: prev.documents.map(doc =>
                                doc.name === message.document.name ? message.document : doc
                            )
                        }));
                        break;
                    case 'document_audit_completed':
                        setPipelineStatus(prev => ({
                            ...prev,
                            documents: prev.documents.map(doc =>
                                doc.name === message.document.name ? message.document : doc
                            )
                        }));
                        break;
                    case 'error':
                        setMessages(prev => [...prev, { type: 'error', text: message.message, timestamp: Date.now() }]);
                        break;
                }
            };

            wsRef.current.onclose = () => {
                setIsConnected(false);
                console.log('WebSocket disconnected, attempting to reconnect...');
                setTimeout(connectWebSocket, 3000);
            };

            wsRef.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setIsConnected(false);
            };
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const startAudit = async () => {
        try {
            const response = await fetch('/api/start_audit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(auditSettings),
            });

            if (!response.ok) {
                throw new Error('Failed to start audit');
            }

            setMessages(prev => [...prev, { type: 'success', text: 'Audit started successfully', timestamp: Date.now() }]);
        } catch (error) {
            setMessages(prev => [...prev, { type: 'error', text: error.message, timestamp: Date.now() }]);
        }
    };

    const getOverallStatusColor = (status) => {
        switch (status) {
            case 'running': return 'text-blue-600';
            case 'completed': return 'text-green-600';
            case 'failed': return 'text-red-600';
            default: return 'text-gray-600';
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <i className="fas fa-users text-blue-600 text-xl"></i>
                            <h1 className="text-xl font-semibold text-gray-900">LLM Council Platform</h1>
                            <div className={`flex items-center space-x-1 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                                <i className={`fas fa-circle text-xs ${isConnected ? '' : 'animate-pulse'}`}></i>
                                <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
                            </div>
                        </div>

                        <div className="flex items-center space-x-4">
                            <div className={`text-sm font-medium ${getOverallStatusColor(pipelineStatus.overall_status)}`}>
                                Status: {pipelineStatus.overall_status}
                            </div>
                            <div className="text-sm text-gray-600">
                                Cost: ${pipelineStatus.total_cost_usd.toFixed(3)}
                            </div>
                            <div className="text-sm text-gray-600">
                                Time: {pipelineStatus.execution_time.toFixed(1)}s
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-6">
                <div className="grid grid-cols-12 gap-6">
                    {/* Left sidebar - Controls */}
                    <div className="col-span-3 space-y-6">
                        <div className="bg-white rounded-lg shadow-sm border p-4">
                            <h2 className="text-lg font-medium text-gray-900 mb-4">
                                <i className="fas fa-cog mr-2"></i>
                                Audit Settings
                            </h2>

                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Documents Path
                                    </label>
                                    <input
                                        type="text"
                                        value={auditSettings.docs_path}
                                        onChange={(e) => setAuditSettings(prev => ({ ...prev, docs_path: e.target.value }))}
                                        className="w-full text-sm border border-gray-300 rounded px-3 py-2"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Model
                                    </label>
                                    <select
                                        value={auditSettings.model}
                                        onChange={(e) => setAuditSettings(prev => ({ ...prev, model: e.target.value }))}
                                        className="w-full text-sm border border-gray-300 rounded px-3 py-2"
                                    >
                                        <option value="gpt-4o">GPT-4o</option>
                                        <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                    </select>
                                </div>

                                <button
                                    onClick={startAudit}
                                    disabled={pipelineStatus.overall_status === 'running'}
                                    className="w-full bg-blue-600 text-white py-2 px-4 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {pipelineStatus.overall_status === 'running' ? (
                                        <>
                                            <i className="fas fa-spinner fa-spin mr-1"></i>
                                            Running...
                                        </>
                                    ) : (
                                        <>
                                            <i className="fas fa-play mr-1"></i>
                                            Start Audit
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        {messages.length > 0 && (
                            <div className="bg-white rounded-lg shadow-sm border p-4">
                                <h3 className="text-sm font-medium text-gray-900 mb-2">Messages</h3>
                                <div className="space-y-2 max-h-32 overflow-y-auto">
                                    {messages.slice(-5).map((message, i) => (
                                        <div
                                            key={message.timestamp}
                                            className={`text-xs p-2 rounded ${
                                                message.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
                                            }`}
                                        >
                                            {message.text}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Main content area */}
                    <div className="col-span-6 space-y-6">
                        {/* Document Pipeline */}
                        <div>
                            <h2 className="text-lg font-medium text-gray-900 mb-4">
                                <i className="fas fa-file-alt mr-2"></i>
                                Document Pipeline
                            </h2>
                            <div className="grid grid-cols-2 gap-4">
                                {pipelineStatus.documents.map((doc) => (
                                    <DocumentCard
                                        key={doc.name}
                                        document={doc}
                                        onClick={setSelectedDocument}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Current Debate Round */}
                        <DebateRoundPanel debateRound={pipelineStatus.current_debate_round} />

                        {/* Research Progress */}
                        <ResearchProgressPanel researchProgress={pipelineStatus.research_progress} />
                    </div>

                    {/* Right sidebar - Council Members */}
                    <div className="col-span-3 space-y-6">
                        <div>
                            <h2 className="text-lg font-medium text-gray-900 mb-4">
                                <i className="fas fa-users mr-2"></i>
                                Council Members
                            </h2>
                            <div className="space-y-3">
                                {pipelineStatus.council_members.map((member, i) => (
                                    <CouncilMemberCard key={`${member.role}-${i}`} member={member} />
                                ))}
                            </div>
                        </div>

                        {/* Selected Document Details */}
                        {selectedDocument && (
                            <div className="bg-white rounded-lg shadow-sm border p-4">
                                <h3 className="text-lg font-medium text-gray-900 mb-3">
                                    Document Details
                                </h3>
                                <div className="space-y-2 text-sm">
                                    <div><strong>Name:</strong> {selectedDocument.name}</div>
                                    <div><strong>Stage:</strong> {selectedDocument.stage}</div>
                                    <div><strong>Status:</strong> <StatusBadge status={selectedDocument.audit_status} /></div>
                                    <div><strong>Words:</strong> {selectedDocument.word_count.toLocaleString()}</div>
                                    {selectedDocument.consensus_score && (
                                        <div><strong>Consensus:</strong> {selectedDocument.consensus_score.toFixed(2)}/5.0</div>
                                    )}
                                    {selectedDocument.last_modified && (
                                        <div><strong>Modified:</strong> {new Date(selectedDocument.last_modified).toLocaleString()}</div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the application
ReactDOM.render(<LLMCouncilApp />, document.getElementById('root'));
