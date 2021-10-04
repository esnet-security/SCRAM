.DEFAULT_GOAL := help

## toggle-prod: configure make to use the production stack
.Phony: toggle-prod
toggle-prod:
	@ln -sf production.yml active.yml

## toggle-local: configure make to use the local stack
.Phony: toggle-local
toggle-local:
	@ln -sf local.yml active.yml

active.yml:
	@ln -sf local.yml active.yml

## behave-all: runs behave inside the containers against all of your features
.Phony: behave-all
behave-all: active.yml
	@docker-compose -f active.yml run django python manage.py behave --no-input --simple

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave: active.yml
	@docker-compose -f active.yml run django python manage.py behave --no-input --simple -i $(FEATURE)

## build: rebuilds all your containers
.Phony: build
build: active.yml
	@docker-compose -f active.yml build

## ci-test: runs all tests just like Gitlab CI does
.Phony: ci-test
ci-test: | build migrate run pytest behave-all

## cleanup: remove local containers and volumes
.Phony: clean
clean: active.yml
	@docker-compose -f active.yml rm -f -s
	@docker volume prune -f

## django-addr: get the IP and ephemeral port assigned to docker:8000
.Phony: django-addr
django-addr: active.yml
	@docker-compose -f active.yml port django 8000

## django-url: get the URL based on http://$(make django-addr)
.Phony: django-url
django-url: active.yml
	@echo http://$$(make django-addr)

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

## migrate: makemigrations and then migrate
.Phony: migrate
migrate: active.yml
	@docker-compose -f active.yml run django python manage.py makemigrations
	@docker-compose -f active.yml run django python manage.py migrate

## pytest: runs pytest inside the containers
.Phony: pytest
pytest: active.yml
	@docker-compose -f active.yml run django pytest

## run: brings up the containers as described in active.yml
.Phony: run
run: active.yml
	@docker-compose -f active.yml up -d

## type-check: static type checking
.Phony: type-check
type-check: active.yml
	@docker-compose -f active.yml run django mypy scram
