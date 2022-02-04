.DEFAULT_GOAL := help
PROJECT_DIR ?= openstats

install:  ## Install flit and openstats
	python -m pip install flit
	python -m flit install

run:  ## Run openstats locally
	python -m streamlit run test.py

py_format:  ## Run black and isort to format the Python codebase
	python -m isort $(PROJECT_DIR) --profile black --multi-line 3
	python -m black $(PROJECT_DIR)

lint:  ## Check linting
	python -m pylint --rcfile=.pylintrc $(PROJECT_DIR)

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[35m%-30s\033[0m %s\n", $$1, $$2}'
