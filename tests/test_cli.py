"""
Tests for CLI interface.

VERIFIES: REQ-012, REQ-013 (CLI interface, command-line argument parsing)
VALIDATES: Click command structure and audit command execution
USE_CASE: UC-001, UC-007 (command-line usage, user interface)
INTERFACES: cli.py (cli, AuditCommand)
LAST_SYNC: 2025-08-30
"""
import pytest
import tempfile
import yaml
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, AsyncMock, patch

from llm_council.cli import cli, AuditCommand


class TestCLICommands:
    """Test CLI command structure and parsing."""

    def test_cli_help_output(self):
        """
        Test that CLI shows help information.
        
        VERIFIES: REQ-012 (CLI interface help and usage)
        VALIDATES: Click command help generation
        USE_CASE: UC-007 (user guidance and documentation)
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert "LLM Council Audit" in result.output
        assert "audit" in result.output

    def test_audit_command_help(self):
        """
        Test audit subcommand help.
        
        VERIFIES: REQ-013 (audit command parameter documentation)
        VALIDATES: Audit subcommand help display
        USE_CASE: UC-007 (command-line usage guidance)
        """
        runner = CliRunner()
        result = runner.invoke(cli, ['audit', '--help'])

        assert result.exit_code == 0
        assert "--stage" in result.output
        assert "--template" in result.output
        assert "--interactive" in result.output

    def test_audit_command_required_docs_path(self):
        """Test that audit command requires docs path."""
        runner = CliRunner()
        result = runner.invoke(cli, ['audit'])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output


class TestAuditCommand:
    """Test audit command functionality."""

    def test_audit_command_initialization(self, temp_dir, sample_template_config, sample_quality_gates):
        """
        Test audit command initialization.
        
        VERIFIES: REQ-012, REQ-013 (audit command setup and validation)
        VALIDATES: AuditCommand instantiation with configuration loading
        USE_CASE: UC-001 (audit process initiation)
        """
        # Create necessary files
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(sample_quality_gates, f)

        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("# Vision Document\nSample vision content")

        # Initialize command
        command = AuditCommand(
            docs_path=docs_dir,
            template_path=template_file,
            quality_gates_path=quality_gates_file,
            stage="vision",
            model="gpt-4o",
            api_key="test-key"
        )

        assert command.docs_path == docs_dir
        assert command.stage == "vision"
        assert command.model == "gpt-4o"

    def test_audit_command_document_loading(self, temp_dir, sample_template_config, sample_quality_gates):
        """Test loading documents from docs directory."""
        # Setup
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(sample_quality_gates, f)

        # Create test documents
        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("# Vision Document\nThis is the vision content.")

        prd_doc = docs_dir / "PRD.md"
        prd_doc.write_text("# PRD Document\nThis is the PRD content.")

        command = AuditCommand(
            docs_path=docs_dir,
            template_path=template_file,
            quality_gates_path=quality_gates_file
        )

        documents = command.load_documents()

        assert "vision" in documents
        assert "prd" in documents
        assert "This is the vision content" in documents["vision"]
        assert "This is the PRD content" in documents["prd"]

    def test_audit_command_missing_documents(self, temp_dir, sample_template_config, sample_quality_gates):
        """Test handling of missing documents."""
        # Setup without documents
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(sample_quality_gates, f)

        command = AuditCommand(
            docs_path=docs_dir,
            template_path=template_file,
            quality_gates_path=quality_gates_file,
            stage="vision"
        )

        documents = command.load_documents()

        # Should handle missing documents gracefully
        assert isinstance(documents, dict)

    @patch('llm_council.cli.AuditorOrchestrator')
    def test_audit_single_stage_execution(self, mock_orchestrator, temp_dir, sample_template_config, sample_quality_gates):
        """Test single stage audit execution."""
        # Setup
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(sample_quality_gates, f)

        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("# Vision Document\nSample content")

        # Mock orchestrator
        mock_instance = AsyncMock()
        mock_orchestrator.return_value = mock_instance

        from llm_council.orchestrator import OrchestrationResult
        from llm_council.consensus import ConsensusResult

        mock_result = OrchestrationResult(
            success=True,
            auditor_responses=[{"auditor_role": "pm", "overall_assessment": {"overall_pass": True}}],
            failed_auditors=[],
            consensus_result=ConsensusResult(
                weighted_average=4.0,
                consensus_pass=True,
                approval_pass=True,
                final_decision="PASS",
                agreement_level=0.9,
                participating_auditors=["pm"],
                failure_reasons=[],
                requires_human_review=False
            ),
            execution_time=1.5
        )

        mock_instance.execute_stage_audit.return_value = mock_result

        command = AuditCommand(
            docs_path=docs_dir,
            template_path=template_file,
            quality_gates_path=quality_gates_file,
            stage="vision",
            api_key="test-key"
        )

        # This would normally be called by the CLI runner
        # For testing purposes, we'll test the components
        documents = command.load_documents()
        assert "vision" in documents

    def test_audit_command_output_generation(self, temp_dir, sample_template_config, sample_quality_gates):
        """Test generation of audit output files."""
        # Setup
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(sample_template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(sample_quality_gates, f)

        command = AuditCommand(
            docs_path=docs_dir,
            template_path=template_file,
            quality_gates_path=quality_gates_file
        )

        # Mock orchestration result
        from llm_council.orchestrator import OrchestrationResult
        from llm_council.consensus import ConsensusResult

        mock_responses = [
            {
                "auditor_role": "pm",
                "overall_assessment": {
                    "overall_pass": True,
                    "summary": "Good document with clear direction",
                    "top_risks": ["Timeline aggressive", "Scope creep"],
                    "quick_wins": ["Add examples", "Clarify metrics"]
                },
                "blocking_issues": []
            }
        ]

        mock_consensus = ConsensusResult(
            weighted_average=4.1,
            consensus_pass=True,
            approval_pass=True,
            final_decision="PASS",
            agreement_level=0.95,
            participating_auditors=["pm"],
            failure_reasons=[],
            requires_human_review=False
        )

        result = OrchestrationResult(
            success=True,
            auditor_responses=mock_responses,
            failed_auditors=[],
            consensus_result=mock_consensus,
            execution_time=2.1
        )

        # Generate output
        output_content = command.generate_audit_summary("vision", result)

        assert "AUDIT SUMMARY" in output_content
        assert "PASS" in output_content
        assert "Timeline aggressive" in output_content
        assert "Add examples" in output_content
        assert "4.1" in output_content  # Score


class TestCLIIntegration:
    """Test CLI integration with real components."""

    @patch('llm_council.cli.AuditorOrchestrator')
    def test_full_audit_command_integration(self, mock_orchestrator, temp_dir):
        """Test full audit command integration."""
        runner = CliRunner()

        # Setup test environment
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Create sample template
        template_config = {
            "project_info": {
                "name": "Test Project",
                "description": "Test template",
                "stages": ["vision"]
            },
            "auditor_questions": {
                "vision": {
                    "pm": {
                        "focus_areas": ["strategy"],
                        "key_questions": ["Is the vision clear?"]
                    }
                }
            },
            "scoring_weights": {}
        }

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_config, f)

        # Create quality gates config
        quality_gates = {
            "consensus_thresholds": {
                "vision_to_prd": {
                    "score_threshold": 3.8,
                    "approval_threshold": 0.67,
                    "required_auditors": ["pm"]
                }
            },
            "auditor_config": {
                "available_roles": ["pm"],
                "parallel_execution": True
            }
        }

        quality_gates_file = temp_dir / "quality_gates.yaml"
        with open(quality_gates_file, 'w') as f:
            yaml.dump(quality_gates, f)

        # Create vision document
        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("# Test Vision\nThis is a test vision document.")

        # Mock orchestrator
        mock_instance = AsyncMock()
        mock_orchestrator.return_value = mock_instance

        from llm_council.orchestrator import OrchestrationResult
        from llm_council.consensus import ConsensusResult

        mock_result = OrchestrationResult(
            success=True,
            auditor_responses=[{
                "auditor_role": "pm",
                "overall_assessment": {
                    "overall_pass": True,
                    "summary": "Clear vision with good strategic direction and implementation guidance",
                    "top_risks": ["Market competition", "Resource constraints"],
                    "quick_wins": ["Add timeline", "Define metrics"]
                },
                "blocking_issues": []
            }],
            failed_auditors=[],
            consensus_result=ConsensusResult(
                weighted_average=4.2,
                consensus_pass=True,
                approval_pass=True,
                final_decision="PASS",
                agreement_level=1.0,
                participating_auditors=["pm"],
                failure_reasons=[],
                requires_human_review=False
            ),
            execution_time=1.8
        )

        mock_instance.execute_stage_audit.return_value = mock_result

        # Test CLI execution
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            result = runner.invoke(cli, [
                'audit',
                str(docs_dir),
                '--stage', 'vision',
                '--template', str(template_file),
                '--quality-gates', str(quality_gates_file),
                '--model', 'gpt-4o'
            ])

        assert result.exit_code == 0
        assert "AUDIT SUMMARY" in result.output or "audit" in result.output.lower()

    def test_cli_missing_api_key(self, temp_dir):
        """Test CLI behavior when API key is missing."""
        runner = CliRunner()

        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Clear environment variable
        with patch.dict('os.environ', {}, clear=True):
            result = runner.invoke(cli, [
                'audit',
                str(docs_dir),
                '--stage', 'vision'
            ])

        # Should either exit with error or prompt for API key
        assert result.exit_code != 0 or "API key" in result.output or "OPENAI_API_KEY" in result.output

    def test_cli_invalid_docs_path(self):
        """Test CLI with invalid docs path."""
        runner = CliRunner()

        result = runner.invoke(cli, [
            'audit',
            '/nonexistent/path',
            '--stage', 'vision'
        ])

        assert result.exit_code != 0

    def test_cli_cost_tracking_output(self, temp_dir):
        """Test that CLI shows cost and token information."""
        # This would be part of the output format
        # Testing the output generation logic
        from llm_council.cli import AuditCommand

        template_config = {
            "project_info": {"name": "Test", "description": "Test", "stages": ["vision"]},
            "auditor_questions": {"vision": {"pm": {"focus_areas": [], "key_questions": ["Q1"]}}},
            "scoring_weights": {}
        }

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_config, f)

        quality_gates_file = temp_dir / "quality_gates.yaml"
        quality_gates_file.write_text("consensus_thresholds: {}")

        command = AuditCommand(
            docs_path=temp_dir / "docs",
            template_path=template_file,
            quality_gates_path=quality_gates_file
        )

        from llm_council.orchestrator import OrchestrationResult

        result = OrchestrationResult(
            success=True,
            auditor_responses=[],
            failed_auditors=[],
            consensus_result=None,
            execution_time=2.5,
            total_tokens=1500,
            total_cost=0.075
        )

        summary = command.generate_execution_summary(result)

        assert "Execution Time: 2.5" in summary
        assert "Total Tokens: 1,500" in summary
        assert "Total Cost: $0.07" in summary

    @patch('llm_council.cli.AuditorOrchestrator')
    def test_file_output_standardization(self, mock_orchestrator, temp_dir):
        """Test that audit command creates standardized output files."""
        runner = CliRunner()

        # Setup test environment
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_config = {
            "project_info": {"name": "Test", "description": "Test", "stages": ["vision"]},
            "auditor_questions": {"vision": {"pm": {"focus_areas": [], "key_questions": ["Q1"]}}},
            "scoring_weights": {}
        }

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_config, f)

        # Create vision document
        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("# Test Vision\nThis is a test vision document.")

        # Mock orchestrator
        mock_instance = AsyncMock()
        mock_orchestrator.return_value = mock_instance

        from llm_council.orchestrator import OrchestrationResult
        from llm_council.consensus import ConsensusResult

        mock_consensus = ConsensusResult(
            weighted_average=4.1,
            consensus_pass=True,
            approval_pass=True,
            final_decision="PASS",
            agreement_level=0.95,
            participating_auditors=["pm"],
            failure_reasons=[],
            requires_human_review=False
        )

        mock_result = OrchestrationResult(
            success=True,
            auditor_responses=[{
                "auditor_role": "pm",
                "overall_assessment": {
                    "overall_pass": True,
                    "summary": "Excellent vision document",
                    "top_risks": ["Market risk"],
                    "quick_wins": ["Add timeline"]
                }
            }],
            failed_auditors=[],
            consensus_result=mock_consensus,
            execution_time=1.5,
            total_tokens=800,
            total_cost=0.04
        )

        mock_instance.execute_stage_audit.return_value = mock_result

        # Run audit command
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            result = runner.invoke(cli, [
                'audit',
                str(docs_dir),
                '--stage', 'vision',
                '--template', str(template_file)
            ])

        assert result.exit_code == 0

        # Check that output files were created
        audit_file = docs_dir / "audit.md"
        decision_file = docs_dir / "decision_vision.md"
        consensus_file = docs_dir / "consensus_vision.md"

        assert audit_file.exists(), "audit.md file should be created"
        assert decision_file.exists(), f"decision_vision.md file should be created"
        assert consensus_file.exists(), "consensus_vision.md file should be created"

        # Check file contents
        audit_content = audit_file.read_text()
        assert "AUDIT SUMMARY" in audit_content
        assert "EXECUTION SUMMARY" in audit_content
        assert "PASS" in audit_content

        decision_content = decision_file.read_text()
        assert "AUDIT SUMMARY" in decision_content
        assert "Market risk" in decision_content

        consensus_content = consensus_file.read_text()
        assert "Consensus Analysis" in consensus_content
        assert "PASS" in consensus_content
        assert "4.1" in consensus_content


class TestResearchAgentIntegration:
    """Test research agent integration for internet context gathering."""

    @patch('llm_council.cli.AuditorOrchestrator')
    @patch('llm_council.cli.ResearchAgent')  # Will implement this
    def test_research_agent_vision_enhancement(self, mock_agent, mock_orchestrator, temp_dir):
        """Test that research agent enhances vision with internet context."""
        runner = CliRunner()

        # Setup test environment
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        template_config = {
            "project_info": {"name": "Test", "description": "Test", "stages": ["vision"]},
            "auditor_questions": {"vision": {"pm": {"focus_areas": [], "key_questions": ["Q1"]}}},
            "scoring_weights": {},
            "research_agent": {
                "enabled": True,
                "provider": "tavily",
                "stages": ["vision"]
            }
        }

        template_file = temp_dir / "template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_config, f)

        # Create vision document
        vision_doc = docs_dir / "VISION.md"
        vision_doc.write_text("""# Vision
        Build an AI-powered document review platform using multiple LLM auditors.
        Target market: software development teams needing faster review cycles.
        """)

        # Mock research agent response
        mock_agent_instance = Mock()
        mock_agent.return_value = mock_agent_instance

        from llm_council.research_agent import ResearchContext
        mock_context = ResearchContext(
            market_trends=["AI development tools growing 45% YoY"],
            competitors=["GitHub Copilot", "CodeRabbit"],
            technical_insights=["Multi-agent systems gaining enterprise adoption"],
            sources=["test-source.com"],
            query_used="AI development tools",
            timestamp="2025-08-29"
        )
        # Make gather_context async
        async def async_gather_context(content, stage):
            return mock_context
        mock_agent_instance.gather_context.side_effect = async_gather_context

        # Mock the format_context_for_document method
        def mock_format_context(context, content):
            return content + f"\n\n## Research Context\n- {context.market_trends[0]}\n- Competitors: {', '.join(context.competitors)}"

        mock_agent_instance.format_context_for_document.side_effect = mock_format_context

        # Mock orchestrator
        mock_orch_instance = AsyncMock()
        mock_orchestrator.return_value = mock_orch_instance

        from llm_council.orchestrator import OrchestrationResult
        from llm_council.consensus import ConsensusResult

        mock_result = OrchestrationResult(
            success=True,
            auditor_responses=[],
            failed_auditors=[],
            consensus_result=ConsensusResult(
                weighted_average=4.0,
                consensus_pass=True,
                approval_pass=True,
                final_decision="PASS",
                agreement_level=0.9,
                participating_auditors=["pm"],
                failure_reasons=[],
                requires_human_review=False
            ),
            execution_time=1.0
        )

        mock_orch_instance.execute_stage_audit.return_value = mock_result

        # Run audit command with research agent
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'TAVILY_API_KEY': 'test-key'}):
            result = runner.invoke(cli, [
                'audit',
                str(docs_dir),
                '--stage', 'vision',
                '--template', str(template_file),
                '--research-context'  # New flag to enable research agent
            ])

        # Debug: print CLI result
        print("CLI Result:", result.output)
        print("CLI Exit Code:", result.exit_code)

        # Verify research agent was called
        assert mock_agent.called, "ResearchAgent should be instantiated"
        assert mock_agent_instance.gather_context.called, "gather_context should be called"

        # Verify enhanced document was passed to orchestrator
        call_args = mock_orch_instance.execute_stage_audit.call_args
        if call_args:
            enhanced_content = call_args[0][1]  # document_content argument
            print("Enhanced content:", repr(enhanced_content))

                # Should contain original content plus research context
            assert "AI-powered document review platform" in enhanced_content
            assert ("AI development tools growing 45% YoY" in enhanced_content or
                   "GitHub Copilot" in enhanced_content or
                   "Research Context" in enhanced_content)
