.PHONY: help dev dev-docker compose-deploy compose-up compose-down compose-logs compose-restart clean test deploy sync add css

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Run Flask development server locally
	cd project && uv run python main.py

css: ## Minify base.css into static/css/base.min.css
	uv run --with rcssmin python3 -c "\
import rcssmin, pathlib; \
src = pathlib.Path('project/static/css/base.css').read_text(); \
pathlib.Path('project/static/css/base.min.css').write_text(rcssmin.cssmin(src))"

dev-docker: ## Run Flask in Docker for development
	docker compose -f docker-compose.development.yml up

# Docker Compose production commands
compose-deploy: ## Pull latest image and deploy with docker compose
	@export $$(grep -v '^#' .env.production | xargs) && \
	docker compose --env-file .env.production pull && \
	docker compose --env-file .env.production up -d && \
	docker image prune -af

compose-up: ## Start services with docker compose (updates web if image changed)
	@export $$(grep -v '^#' .env.production | xargs) && \
	docker compose --env-file .env.production pull web && \
	docker compose --env-file .env.production up -d web && \
	docker image prune -af

compose-down: ## Stop and remove docker compose services
	docker compose --env-file .env.production down

compose-logs: ## View logs from docker compose services
	docker compose --env-file .env.production logs -f

compose-restart: ## Restart docker compose services
	docker compose --env-file .env.production restart

logs: ## View logs from running containers
	docker compose --env-file .env.production logs -f

clean: ## Clean up Python cache and Docker resources
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	docker system prune -af

install: ## Install Python dependencies
	cd project && uv sync

test: ## Run tests (when implemented)
	cd project && uv run pytest

deploy: ## Alias for compose-deploy
	@export $$(grep -v '^#' .env.production | xargs) && \
	docker compose --env-file .env.production pull && \
	docker compose --env-file .env.production up -d && \
	docker image prune -af

sync: ## Sync dependencies to lock file
	cd project && uv sync

add: ## Add a new dependency (usage: make add PACKAGE=flask-cors)
	cd project && uv add $(PACKAGE)
