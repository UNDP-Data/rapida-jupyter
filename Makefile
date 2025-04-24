.PHONY: help test build down shell

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  shell            to shell in dev mode"
	@echo "  build            to build docker image"
	@echo "  up               to start docker containers"
	@echo "  down             to destroy docker containers"


shell:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Shelling in dev mode"
	@echo "------------------------------------------------------------------"
	docker compose -f docker-compose.yaml run --remove-orphans --entrypoint /bin/bash rapida_jupyter


build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building Docker image"
	@echo "------------------------------------------------------------------"
	docker compose -f docker-compose.yaml build --build-arg PRODUCTION=$(PRODUCTION)

up:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Launch docker containers"
	@echo "------------------------------------------------------------------"
	docker compose -f docker-compose.yaml up

down:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Destroy docker containers"
	@echo "------------------------------------------------------------------"
	docker compose -f docker-compose.yaml down


