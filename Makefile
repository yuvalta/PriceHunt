.PHONY: build up down logs clean test lint

# Default target
all: build up

# Build the Docker image
build:
	docker-compose build

# Start the application
up:
	docker-compose up -d

# Stop the application
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up Docker resources
clean:
	docker-compose down -v
	docker system prune -f

# Run tests
test:
	docker-compose run --rm app pytest

# Run linter
lint:
	docker-compose run --rm app flake8 .

# Restart the application
restart:
	docker-compose restart

# Check application status
status:
	docker-compose ps

# View application logs
logs:
	docker-compose logs -f

# Shell into the container
shell:
	docker-compose exec app /bin/bash

# Help command
help:
	@echo "Available commands:"
	@echo "  make build    - Build the Docker image"
	@echo "  make up       - Start the application"
	@echo "  make down     - Stop the application"
	@echo "  make logs     - View application logs"
	@echo "  make clean    - Clean up Docker resources"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linter"
	@echo "  make restart  - Restart the application"
	@echo "  make status   - Check application status"
	@echo "  make shell    - Shell into the container"
	@echo "  make help     - Show this help message" 