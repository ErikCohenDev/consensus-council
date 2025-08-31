# How to Run System Validation

This document explains how to validate the Idea Operating System using our comprehensive test suite.

## Quick Start

### 1. Check System Status

```bash
python3 scripts/system-status.py --verbose
```

This performs a quick health check of all system components.

### 2. Run Basic Validation

```bash
python3 scripts/run-basic-validation.py --verbose
```

This runs smoke tests + basic E2E tests that we know work.

### 3. Run Complete Validation (Future)

```bash
./run-validation.sh --quick
```

This will run the complete validation suite once all features are implemented.

## Validation Levels

### 🔥 Smoke Tests

**Purpose**: Verify core components can be imported and initialized  
**Runtime**: ~0.3 seconds  
**Command**: `python3 scripts/smoke-test.py --verbose`

**Tests**:

- Import core modules
- Model validation
- Service initialization  
- Config loading
- Schema validation

### 🧪 Basic E2E Tests

**Purpose**: Validate core workflows work end-to-end  
**Runtime**: ~0.4 seconds  
**Command**: `PYTHONPATH=src python3 -m pytest tests/e2e/test_basic_system.py -v --no-cov`

**Tests**:

- Model creation and validation
- Schema validation and serialization
- Neo4j configuration
- Multi-model client initialization
- Complete idea processing workflow
- System readiness metrics
- Founder journey basic flow
- End-to-end data integration

### 🚀 Advanced E2E Tests (Future)

**Purpose**: Test complex user journeys with real integrations  
**Runtime**: ~5-10 minutes  
**Command**: `./run-validation.sh --full`

**Tests** (when implemented):

- Founder journey with YC/McKinsey/Lean paradigms
- Product Manager requirements traceability
- Engineer spec-to-code workflow
- Team collaboration and coordination
- Complete system with Neo4j + LLMs

## Current Status

### ✅ Working (13/13 tests pass)

- All smoke tests
- All basic E2E tests
- Core system validation
- Basic founder journey
- Data model validation

### 🔧 In Development

- Neo4j database operations
- Council debate system
- Question generation engine
- Research integration
- Advanced user journeys

## Troubleshooting

### Common Issues

**Import Errors**:

```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python path
export PYTHONPATH=src
```

**Neo4j Connection Issues**:

```bash
# For advanced tests (not needed for basic validation)
docker run -d --name neo4j-test -p 7687:7687 -e NEO4J_AUTH=neo4j/test-password neo4j:5.15-community
```

**Test Failures**:

```bash
# Run individual test for debugging
PYTHONPATH=src python3 -m pytest tests/e2e/test_basic_system.py::TestBasicSystemFunctionality::test_model_creation_and_validation -v
```

### Validation Modes

**Quick Check** (recommended for development):

```bash
python3 scripts/run-basic-validation.py
```

**Verbose Output** (for debugging):

```bash
python3 scripts/run-basic-validation.py --verbose
```

**System Health Only**:

```bash
python3 scripts/system-status.py
```

## Success Criteria

### ✅ Basic Validation Success

- All smoke tests pass (5/5)
- All basic E2E tests pass (8/8)
- System readiness score: 100%
- Founder journey success rate: ≥80%

### 🎯 Advanced Validation Success (Future)

- All user journey tests pass
- Neo4j integration working
- Council consensus achieved
- Research integration functional
- Complete traceability validated

## Integration with Development

### Pre-Commit Validation

```bash
# Add to your development workflow
python3 scripts/run-basic-validation.py && echo "✅ Ready to commit"
```

### CI/CD Integration

```bash
# For continuous integration
./run-validation.sh --quick --no-setup
```

### Feature Development

1. Run basic validation before starting: `python3 scripts/run-basic-validation.py`
2. Develop your feature
3. Add tests to appropriate test file
4. Run validation again to ensure no regressions
5. Commit when validation passes

## Next Steps

As we implement more features, we'll:

1. **Expand E2E Tests**: Add tests for new functionality
2. **Enable Advanced Tests**: Activate the complex user journey tests
3. **Add Integration Tests**: Test with real Neo4j and LLM APIs
4. **Performance Testing**: Add performance validation
5. **Production Readiness**: Add deployment and monitoring validation

The validation framework is designed to grow with the system while maintaining confidence in core functionality.
