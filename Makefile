.PHONY: help build run stop clean logs test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the Docker image
	docker-compose build

run: ## Start the API service
	docker-compose up -d

stop: ## Stop the API service
	docker-compose down

clean: ## Stop and remove containers, networks, and images
	docker-compose down --rmi all --volumes --remove-orphans

logs: ## View API logs
	docker-compose logs -f generic-dynamodb-api

test: ## Run tests (if available)
	@echo "No tests configured yet"

setup: ## Initial setup - copy env file
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from env.example"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env file already exists"; \
	fi

status: ## Check service status
	docker-compose ps

restart: ## Restart the API service
	docker-compose restart generic-dynamodb-api 