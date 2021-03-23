.DEFAULT_GOAL := help

## behave-all: runs behave inside the containers against all of your features
.Phony: behave-all
behave-all:
	docker-compose -f local.yml run django python manage.py behave --no-input

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave:
	docker-compose -f local.yml run django python manage.py behave --no-input -i $(FEATURE)

## build: rebuilds all your containers
build:
	docker-compose -f local.yml build

## ci-test: runs all tests just like Gitlab CI does
.Phony: ci-test
ci-test:
	docker-compose -f local.yml run --rm django python manage.py migrate && \
	docker-compose -f local.yml up -d && \
	docker-compose -f local.yml run django pytest; \
	docker-compose -f local.yml run django python manage.py behave --no-input

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

## migrate: makemigrations and then migrate
.Phony: migrate
migrate:
	docker-compose -f local.yml run django python manage.py makemigrations && \
	docker-compose -f local.yml run django python manage.py migrate

## pytest: runs pytest inside the containers
.Phony: pytest
pytest:
	docker-compose -f local.yml run django pytest

## run: brings up the containers as described in local.yml
.Phony: run
run:
	docker-compose -f local.yml up -d
