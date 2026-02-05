# Convenience Makefile for common tasks
.PHONY: start start-dev build-prod up-prod migrate test ci clean

start:
	docker-compose up --build

start-dev:
	./scripts/start-dev.sh

build-prod:
	docker-compose -f docker-compose.prod.yml build

up-prod:
	docker-compose -f docker-compose.prod.yml up -d

migrate:
	bash backend/scripts/run_migrations.sh

test:
	pytest backend/tests

ci:
	# Run CI-like local checks
	make migrate
	make test

clean:
	docker-compose down -v --remove-orphans
	rm -rf frontend/dist
