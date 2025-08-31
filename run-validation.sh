#!/bin/bash
# Complete System Validation Runner
# This script runs comprehensive validation of the Idea Operating System

set -e  # Exit on any error

echo "🚀 Starting Complete Idea Operating System Validation"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "scripts/validate-complete-system.py" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required"
    exit 1
fi

# Check if Docker is available and running
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is required for Neo4j test database"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    exit 1
fi

# Parse command line arguments
VALIDATION_MODE="--full"
USER_JOURNEY=""
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            VALIDATION_MODE="--quick"
            shift
            ;;
        --trace-only)
            VALIDATION_MODE="--trace-only"
            shift
            ;;
        --user-journey)
            USER_JOURNEY="--user-journey $2"
            shift 2
            ;;
        --skip-setup)
            EXTRA_ARGS="$EXTRA_ARGS --skip-setup"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick           Quick validation (skip performance tests)"
            echo "  --trace-only      Run only traceability validation"
            echo "  --user-journey    Run specific user journey (founder|pm|engineer|team|complete_system)"
            echo "  --skip-setup      Skip environment setup"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Full validation"
            echo "  $0 --quick           # Quick validation"
            echo "  $0 --user-journey founder  # Test founder journey only"
            echo "  $0 --trace-only      # Traceability validation only"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "📋 Validation Mode: $VALIDATION_MODE"
if [ -n "$USER_JOURNEY" ]; then
    echo "👤 User Journey: $USER_JOURNEY"
fi
echo "=================================================="

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    python3 -m pip install -r requirements.txt --quiet
    echo "   ✅ Dependencies installed"
fi

# Run the complete validation
echo "🧪 Starting validation..."
python3 scripts/validate-complete-system.py $VALIDATION_MODE $USER_JOURNEY $EXTRA_ARGS

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 VALIDATION SUCCESSFUL!"
    echo "✅ Idea Operating System is ready for production"
    echo "✅ All tests passed and system is healthy"
    echo ""
    echo "Next steps:"
    echo "  • Deploy to staging environment"
    echo "  • Run user acceptance testing"
    echo "  • Prepare production deployment"
else
    echo ""
    echo "❌ VALIDATION FAILED!"
    echo "🔧 Please fix the issues identified above"
    echo ""
    echo "Common fixes:"
    echo "  • Check Neo4j is running: docker ps"
    echo "  • Verify Python dependencies: pip install -r requirements.txt"
    echo "  • Review test failures in validation_results.json"
    echo "  • Check system logs for detailed error information"
    exit 1
fi