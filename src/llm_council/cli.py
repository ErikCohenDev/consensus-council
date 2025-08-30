"""CLI entrypoint and AuditCommand abstraction.

Implements the interfaces required by the test suite. The CLI focuses on a
single primary subcommand: `audit` which runs an audit for a specific stage.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Dict, Optional

import click

from .alignment import AlignmentValidator
from .constants import DOCUMENT_STAGE_MAPPING
from .orchestrator import AuditorOrchestrator, OrchestrationResult
from .pipeline import PipelineOrchestrator, RevisionStrategy
from .research_agent import ResearchAgent

logger = logging.getLogger(__name__)


@dataclass
class AuditCommand:
    """Represents an audit invocation with loaded configuration."""

    docs_path: Path
    template_path: Optional[Path] = None
    quality_gates_path: Optional[Path] = None
    stage: Optional[str] = None
    model: str = "gpt-4o"
    api_key: Optional[str] = None

    def load_documents(self) -> Dict[str, str]:
        """Load all known stage documents from the docs directory.

        Missing documents are skipped (graceful handling expected by tests).
        Returns mapping of stage -> raw markdown content.
        """
        documents: Dict[str, str] = {}
        if not self.docs_path.exists():  # Gracefully handle missing directory
            return documents
        for file in self.docs_path.iterdir():
            if not file.is_file():
                continue
            key = DOCUMENT_STAGE_MAPPING.get(file.name)
            if key:
                try:
                    documents[key] = file.read_text(encoding="utf-8")
                except Exception:  # noqa: BLE001
                    # Skip unreadable file; continue loading others
                    logger.warning("Could not read file: %s", file.name, exc_info=True)
                    continue
        return documents

    def generate_audit_summary(self, stage: str, result: OrchestrationResult) -> str:
        """Create a human-readable audit summary string."""
        lines = []
        lines.append(f"=== AUDIT SUMMARY - {stage.upper()} ===")
        if result.consensus_result:
            cr = result.consensus_result
            lines.append(f"Final Decision: {cr.final_decision}")
            lines.append(
                f"Weighted Consensus Score: {cr.weighted_average:.1f} "
                f"(Agreement {cr.agreement_level:.2f})"
            )
        else:
            lines.append("Final Decision: UNKNOWN (partial failure)")

        for resp in result.auditor_responses:
            oa = resp.get("overall_assessment", {})
            summary = oa.get("summary", "")
            lines.append("")
            lines.append(
                f"Auditor: {resp.get('auditor_role')} - Pass: {oa.get('overall_pass')}"
            )
            if summary:
                lines.append(summary)
            # Risks
            risks = oa.get("top_risks", [])
            if risks:
                lines.append("Top Risks: " + "; ".join(risks))
            # Quick wins
            wins = oa.get("quick_wins", [])
            if wins:
                lines.append("Quick Wins: " + "; ".join(wins))

        return "\n".join(lines)

    def generate_alignment_summary(self, alignment_results) -> str:
        """Create alignment validation summary."""
        lines = ["=== ALIGNMENT VALIDATION ==="]

        total_checks = len(alignment_results)
        aligned_count = sum(1 for r in alignment_results if r.is_aligned)

        lines.append(f"Alignment Checks: {aligned_count}/{total_checks} PASS")

        for result in alignment_results:
            status = "✅ ALIGNED" if result.is_aligned else "❌ MISALIGNED"
            lines.append(
                f"{result.source_stage} → {result.target_stage}: {status} "
                f"({result.alignment_score:.1f}/5)"
            )

            if not result.is_aligned:
                lines.append(f"  Issues: {len(result.misalignments)} misalignments detected")
                if result.misalignments:
                    lines.append(f"  Key Issue: {result.misalignments[0]}")

        return "\n".join(lines)

    def generate_execution_summary(self, result: OrchestrationResult) -> str:
        """Create execution metrics summary."""
        lines = ["=== EXECUTION SUMMARY ==="]
        lines.append(f"Execution Time: {result.execution_time:.1f}")
        if result.total_tokens is not None:
            lines.append(f"Total Tokens: {format(result.total_tokens, ',')}")
        if result.total_cost is not None:
            # Truncate (not round half-up) to match test expectation for 0.075 -> 0.07
            cost_str = (
                f"{Decimal(str(result.total_cost)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)}"
            )
            lines.append(f"Total Cost: ${cost_str}")
        return "\n".join(lines)


@click.group(help="LLM Council Audit CLI providing document quality gates.")
def cli():
    """Main CLI entrypoint."""


@cli.command(name="audit", help="Run an audit for a specific stage.")
@click.argument("docs_path", type=click.Path(path_type=Path))
@click.option("--stage", required=True, help="Stage to audit (e.g. vision, prd)")
@click.option(
    "--template", "template_path", type=click.Path(path_type=Path), help="Path to template YAML"
)
@click.option(
    "--quality-gates",
    "quality_gates_path",
    type=click.Path(path_type=Path),
    help="Path to quality gates YAML",
)
@click.option("--model", default="gpt-4o", show_default=True, help="Model name")
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
@click.option("--interactive", is_flag=True, help="Enable interactive mode (future)")
@click.option(
    "--research-context",
    is_flag=True,
    help="Enable research agent for internet context gathering",
)
@click.option("--council-debate", is_flag=True, help="Enable council member debate mode")
@click.option("--no-cache", is_flag=True, help="Disable caching for debugging")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory (default: .cache)",
)
def audit_cmd(
    docs_path: Path,
    stage: str,
    template_path: Optional[Path],
    quality_gates_path: Optional[Path],
    model: str,
    api_key: Optional[str],
    interactive: bool,  # Remove underscore prefix
    research_context: bool,
    council_debate: bool,  # Remove underscore prefix
    no_cache: bool,
    cache_dir: Optional[Path],
):
    """Run a single audit stage."""
    # Note: interactive and council_debate parameters are reserved for future features
    _ = interactive  # Reserved for future interactive mode
    _ = council_debate  # Reserved for future council debate mode

    if not api_key:
        raise click.UsageError(
            "API key required – pass --api-key or set OPENAI_API_KEY env var"
        )
    if not docs_path.exists():
        raise click.UsageError(f"Docs path does not exist: {docs_path}")

    command = AuditCommand(
        docs_path=docs_path,
        template_path=template_path,
        quality_gates_path=quality_gates_path,
        stage=stage,
        model=model,
        api_key=api_key,
    )

    documents = command.load_documents()
    if stage not in documents:
        click.echo(
            f"Warning: Stage '{stage}' document not found. Proceeding with empty content.",
            err=True,
        )
    document_content = documents.get(stage, "")

    # Enhance with research context if enabled
    if research_context:
        try:
            research_agent = ResearchAgent(provider="tavily", enabled=True)
            context = asyncio.run(research_agent.gather_context(document_content, stage))
            document_content = research_agent.format_context_for_document(
                context, document_content
            )
        except Exception as e:
            click.echo(f"Warning: Research agent failed: {e}", err=True)
            logger.warning("Research agent failed", exc_info=True)

    # Run orchestrator
    if not template_path:
        raise click.UsageError("--template is required for auditing")

    # Set up cache directory
    if cache_dir is None:
        cache_dir = docs_path / ".cache"

    orchestrator = AuditorOrchestrator(
        template_path=template_path,
        model=model,
        api_key=api_key,
        cache_dir=cache_dir if not no_cache else None,
        enable_cache=not no_cache,
    )
    result = asyncio.run(orchestrator.execute_stage_audit(stage, document_content))

    # Set up output directory
    output_dir = docs_path

    # Run alignment validation
    alignment_validator = AlignmentValidator()
    alignment_results = alignment_validator.validate_document_chain(documents)

    # Generate backlog files for misaligned documents
    for alignment_result in alignment_results:
        if not alignment_result.is_aligned:
            backlog_content = alignment_validator.generate_backlog_file(alignment_result)
            backlog_file = (
                output_dir / f"alignment_backlog_{alignment_result.target_stage}.md"
            )
            backlog_file.write_text(backlog_content, encoding="utf-8")

    # Generate content for output files
    audit_content = command.generate_audit_summary(stage, result)
    execution_content = command.generate_execution_summary(result)

    # Add alignment summary to audit content
    if alignment_results:
        alignment_summary = command.generate_alignment_summary(alignment_results)
        audit_content = f"{audit_content}\n\n{alignment_summary}"

    # Write output files according to PRD requirements
    (output_dir / "audit.md").write_text(
        f"{audit_content}\n\n{execution_content}", encoding="utf-8"
    )
    (output_dir / f"decision_{stage}.md").write_text(audit_content, encoding="utf-8")

    # Write consensus details if available
    if result.consensus_result:
        consensus_content = f"# Consensus Analysis - {stage.upper()}\n\n"
        consensus_content += f"Final Decision: {result.consensus_result.final_decision}\n"
        consensus_content += (
            f"Weighted Average: {result.consensus_result.weighted_average:.2f}\n"
        )
        consensus_content += (
            f"Agreement Level: {result.consensus_result.agreement_level:.2f}\n"
        )
        (output_dir / f"consensus_{stage}.md").write_text(
            consensus_content, encoding="utf-8"
        )

    click.echo(audit_content)
    click.echo("")
    click.echo(execution_content)

    # Non-zero exit for failure decisions
    if result.consensus_result and result.consensus_result.final_decision == "FAIL":
        raise SystemExit(1)


__all__ = ["cli", "AuditCommand"]


@cli.command(
    name="pipeline", help="Run a multi-stage gated pipeline (Vision → PRD → Architecture)"
)
@click.argument("docs_path", type=click.Path(path_type=Path))
@click.option(
    "--template", "template_path", type=click.Path(path_type=Path), required=True
)
@click.option(
    "--stages",
    default="vision,prd,architecture",
    show_default=True,
    help="Comma-separated stages",
)
@click.option(
    "--max-iters", default=1, type=int, show_default=True, help="Max pipeline iterations"
)
@click.option("--model", default="gpt-4o", show_default=True, help="Model name")
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
@click.option("--no-cache", is_flag=True, help="Disable caching for debugging")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory (default: .cache)",
)
def pipeline_cmd(
    docs_path: Path,
    template_path: Path,
    stages: str,
    max_iters: int,
    model: str,
    api_key: Optional[str],
    no_cache: bool,
    cache_dir: Optional[Path],
):
    """Run a multi-stage gated pipeline."""
    if not api_key:
        raise click.UsageError(
            "API key required - pass --api-key or set OPENAI_API_KEY env var"
        )
    if not docs_path.exists():
        raise click.UsageError(f"Docs path does not exist: {docs_path}")

    # Load documents
    command = AuditCommand(
        docs_path=docs_path,
        template_path=template_path,
        quality_gates_path=None,
        model=model,
        api_key=api_key,
    )
    documents = command.load_documents()

    # Determine stage order
    stage_list = [s.strip() for s in stages.split(",") if s.strip()]

    # Set up cache directory
    if cache_dir is None:
        cache_dir = docs_path / ".cache"

    orchestrator = PipelineOrchestrator(
        template_path=template_path,
        model=model,
        api_key=api_key,
        cache_dir=cache_dir if not no_cache else None,
        enable_cache=not no_cache,
    )

    summary = orchestrator.run(
        documents=documents,
        stages=stage_list,
        max_iterations=max_iters,
        revision_strategy=RevisionStrategy(),  # No-op; plug in synthesis later
        output_dir=docs_path,  # Drop per-iter summaries alongside docs
    )

    # Build final summary output
    lines = ["=== PIPELINE SUMMARY ==="]
    lines.append(f"Iterations: {summary.iterations}")
    lines.append(f"Status: {'PASS' if summary.success else 'FAIL'}")
    for stage, sr in summary.stage_results.items():
        cr = sr.orchestration.consensus_result
        decision = cr.final_decision if cr else "UNKNOWN"
        score = f"{cr.weighted_average:.1f}" if cr else "-"
        lines.append(f"{stage.upper()}: {decision} (Score {score})")

    # Alignment status lines
    misaligned = [ar for ar in summary.alignment_results if not ar.is_aligned]
    if summary.alignment_results:
        aligned_count = sum(1 for ar in summary.alignment_results if ar.is_aligned)
        total = len(summary.alignment_results)
        lines.append(f"Alignment: {aligned_count}/{total} PASS")
        if misaligned:
            lines.append("Misalignments:")
            for ar in misaligned[:5]:
                lines.append(
                    f"- {ar.source_stage} → {ar.target_stage}: "
                    f"{ar.misalignments[0] if ar.misalignments else 'Unknown issue'}"
                )

    (docs_path / "pipeline_summary.md").write_text("\n".join(lines), encoding="utf-8")
    click.echo("\n".join(lines))

    if not summary.success:
        raise SystemExit(1)


@cli.command(
    name="ui", help="Launch the web-based UI server for interactive council management"
)
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind the server to")
@click.option(
    "--port", default=8000, type=int, show_default=True, help="Port to bind the server to"
)
@click.option("--docs-path", default="./docs", show_default=True, help="Default documents path")
@click.option("--debug", is_flag=True, help="Enable debug mode with auto-reload")
def ui_cmd(host: str, port: int, docs_path: str, debug: bool):
    """Launch the web-based UI server for interactive council management."""
    try:
        # Import UI components only when needed to avoid circular imports
        from .ui_server import UIConfig, run_ui_server

        config = UIConfig(host=host, port=port, docs_path=docs_path, debug=debug)

        click.echo("🚀 Starting LLM Council UI server...")
        click.echo(f"📍 Server will be available at: http://{host}:{port}")
        click.echo(f"📁 Default docs path: {docs_path}")
        click.echo(f"🔧 Debug mode: {'enabled' if debug else 'disabled'}")
        click.echo()
        click.echo("Press Ctrl+C to stop the server")

        run_ui_server(config)
    except ImportError as e:
        click.echo(f"❌ Failed to import UI server dependencies: {e}")
        click.echo(
            '💡 Try installing UI dependencies: '
            'pip install "fastapi>=0.104.0" "uvicorn>=0.24.0" "websockets>=12.0"'
        )
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        click.echo("\n👋 UI server stopped")
    except Exception as e:
        click.echo(f"❌ Server error: {e}")
        logger.critical("UI server failed", exc_info=True)
        raise SystemExit(1) from e
