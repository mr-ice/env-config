help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} \
    /^[$()% a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1,$$2 } \
    /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

style:  ## Format code with ruff
	ruff format

lint:  ## Check code with ruff
	ruff check

test:  ## Run pytest
	PYTHONPATH=src pytest -q

test-cov:  ## Run pytest with coverage
	PYTHONPATH=src pytest -q --cov=src --cov-report=term --cov-report=xml:coverage.xml

ptw:  ## Run pytest-watch (if installed)
	ptw

clean:  ## Remove pycache and build artifacts
	rm -rf build dist *.egg-info .pytest_cache **/__pycache__
