import { useState } from "react";
import { usePipelineState } from "@/stores/appStore";

export const AuditPage = () => {
	const { pipelineProgress } = usePipelineState();
	const [starting, setStarting] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const startAudit = async () => {
		setStarting(true);
		setError(null);
		try {
			// Create a run for a simple local project (MVP)
			const projectId = "local";
			const res = await fetch(`/api/projects/${projectId}/runs`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				// Include docsPath as a fallback server-side for MVP
				body: JSON.stringify({
					docsPath: "./docs",
					stage: undefined,
					model: "gpt-4o",
				}),
			});
			if (!res.ok) throw new Error(`Failed to start audit (${res.status})`);
		} catch (e) {
			setError(e instanceof Error ? e.message : String(e));
		} finally {
			setStarting(false);
		}
	};

	return (
		<div className="space-y-4">
			<h1 className="text-xl font-semibold">Audit</h1>
			<button
				data-testid="start-run"
				onClick={startAudit}
				disabled={starting}
				className="px-3 py-2 border rounded disabled:opacity-50"
			>
				{starting ? "Starting…" : "Start Audit"}
			</button>
			{error && <div className="text-sm text-red-600">{error}</div>}

			<div className="border rounded p-3">
				<div className="font-medium mb-2">Current Status</div>
				<div className="text-sm">
					Overall:{" "}
					<span className="capitalize">
						{pipelineProgress?.overallStatus ?? "idle"}
					</span>
				</div>
			</div>
		</div>
	);
};
