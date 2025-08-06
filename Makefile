# Makefile for smart-recipe-runner

.PHONY: test test-verbose test-coverage test-unit test-integration install-deps clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-unit      - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  install-deps   - Install test dependencies"
	@echo "  clean          - Clean up temporary files"

# Install dependencies
install-deps:
	pip install -r lib/requirements.txt

# Run all tests
test:
	python -m pytest tests/ -v

# Run tests with verbose output
test-verbose:
	python -m pytest tests/ -v -s

# Run tests with coverage
test-coverage:
	python -m pytest tests/ --cov=lib --cov-report=html --cov-report=term

# Run only unit tests
test-unit:
	python -m pytest tests/ -m "not integration" -v

# Run only integration tests  
test-integration:
	python -m pytest tests/ -m integration -v

# Run specific test file
test-config:
	python -m pytest tests/test_config_manager.py -v

test-runner:
	python -m pytest tests/test_recipe_runner.py -v

# Clean up
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
