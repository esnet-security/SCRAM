# It'd be nice to keep these in sync with the defaults of the Dockerfiles
PYTHON_IMAGE_VER ?= 3.12
POSTGRES_IMAGE_VER ?= 18

ACT := act --rm --container-options "--privileged -u root" --container-architecture linux/amd64 --platform ubuntu-latest=catthehacker/ubuntu:act-latest

.DEFAULT_GOAL := help

## toggle-prod: configure make to use the production stack
.Phony: toggle-prod
toggle-prod:
	@ln -sf compose.override.production.yml compose.override.yml

## toggle-local: configure make to use the local stack
.Phony: toggle-local
toggle-local:
	@ln -sf compose.override.local.yml compose.override.yml

# Since toggle-(local|prod) are phony targets, this file is not
# tracked to compare if its "newer" so running another target with
# this as a prereq will not run this target again. That would
# overwrite compose.override.yml back to compose.override.local.yml no
# matter what, which is bad. Phony targets prevents this
## compose.override.yml: creates file compose.override.yml on first run (as a prereq)
compose.override.yml:
	@ln -sf compose.override.local.yml compose.override.yml

## behave-all: runs behave inside the containers against all of your features
.Phony: behave-all
behave-all: compose.override.yml
	@docker compose run --rm -w /app -e PYTHONPATH=/app/src django coverage run -a src/manage.py behave --no-input --simple

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave: compose.override.yml
	@docker compose run --rm -w /app -e PYTHONPATH=/app/src django python src/manage.py behave --no-input --simple -i $(FEATURE)

## integration-tests: runs multi-instance system tests against docker compose running containers
.Phony: integration-tests
integration-tests: run
	@docker compose exec -T -w /app -e PYTHONPATH=/app/src django coverage run -a src/manage.py behave --no-input --use-existing-database src/scram/route_manager/tests/integration

## behave-translator
.Phony: behave-translator
behave-translator: compose.override.yml
	@docker compose exec -T translator behave /app/tests/acceptance/features

## build: rebuilds all your containers or a single one if CONTAINER is specified
.Phony: build
build: compose.override.yml
	@docker compose build --build-arg PYTHON_IMAGE_VER=$(PYTHON_IMAGE_VER) --build-arg POSTGRES_IMAGE_VER=$(POSTGRES_IMAGE_VER) $(CONTAINER)
	@docker compose up -d --no-deps $(CONTAINER)
	@docker compose restart $(CONTAINER)

## coverage.xml: create coverage files per-project (CI does this differently!)
coverage.xml: pytest behave-all integration-tests test-scheduler
	@docker compose run --rm -w /app django coverage report
	@docker compose run --rm -w /app django coverage xml

## test-django: start everything and then run all django tests (pytest + behave + integration) generating coverage.
.Phony: test-django
test-django: toggle-local build migrate run coverage.xml

## test-scheduler: runs scheduler package tests with coverage
.Phony: test-scheduler
test-scheduler:
	@cd scheduler && uv run pytest

## test-translator: start everything and run translator behave tests locally
.Phony: test-translator
test-translator: toggle-local build migrate run behave-translator

## test-scripts: runs scripts package tests
.Phony: test-scripts
test-scripts:
	@cd scripts && uv run pytest tests/

## test: start everything and run all tests (django + translator + scheduler)
.Phony: test
test: test-django test-translator test-scheduler test-scripts

## ci-test: runs all CI workflows locally via act; requires act (`brew install act`)
.Phony: ci-test
ci-test:
	@$(ACT) push --workflows .github/workflows/ruff.yml
	@$(ACT) push --workflows .github/workflows/scripts.yml
	@$(ACT) push --workflows .github/workflows/scheduler.yml
	@$(ACT) push --workflows .github/workflows/translator.yml
	@$(ACT) push --workflows .github/workflows/django.yml
# 	@$(ACT) push --workflows .github/workflows/type-check.yml

## clean: remove local containers and volumes
.Phony: clean
clean: compose.override.yml
	@docker compose rm -f -s
	@docker volume prune -f

## collect-static: run collect static admin command
.Phony: collectstatic
collectstatic: compose.override.yml
	@docker compose run --rm django python manage.py collectstatic

## django-addr: get the IP and ephemeral port assigned to docker:8000
.Phony: django-addr
django-addr: compose.override.yml
	@docker compose port django 8000

## django-url: get the URL based on http://$(make django-addr)
.Phony: django-url
django-url: compose.override.yml
	@echo http://$$(make django-addr)

## django-open: open a browser for http://$(make django-addr)
.Phony: django-open
django-open: compose.override.yml
	@open http://$$(make django-addr)

## down: turn down docker compose stack
.Phony: down
down: compose.override.yml
	@docker compose down

## exec: executes a given command on a given container (append CONTAINER=container_name_here and COMMAND=command_here)
.Phony: exec
exec: compose.override.yml
	@docker compose exec $(CONTAINER) $(COMMAND)

## gobgp-neighbor: shows the gobgp neighbor information (append neighbor IP for specific information)
.Phony: gobgp-neighbor
gobgp-neighbor: compose.override.yml
	@docker compose exec gobgp gobgp neighbor $(NEIGHBOR)

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

# TODO: When we move to flowspec this -a flag with change
## list-routes: list gobgp routes
.Phony: list-routes
list-routes: compose.override.yml
	@docker compose exec gobgp gobgp global rib -a ipv4
	@docker compose exec gobgp gobgp global rib -a ipv6

## migrate: makemigrations and then migrate
.Phony: migrate
migrate: compose.override.yml
	@docker compose run --rm django python manage.py makemigrations
	@docker compose run --rm django python manage.py migrate

## pass-reset: change admin's password
.Phony: pass-reset
pass-reset: compose.override.yml
	@docker compose run --rm django python manage.py changepassword admin

## pytest: runs pytest inside the containers
.Phony: pytest
pytest: compose.override.yml
	@docker compose run --rm -w /app -e PYTHONPATH=/app/src django coverage run -m pytest

## run: brings up the containers as described in compose.override.yml
.Phony: run
run: compose.override.yml
	@docker compose up -d


## stop: turns off running containers
.Phony: stop
stop: compose.override.yml
	@docker compose stop

## tail-log: tail a docker container's logs (append CONTAINER=container_name_here)
.Phony: tail-log
tail-log: compose.override.yml
	@docker compose logs -f $(CONTAINER)

## type-check: static type checking
.Phony: type-check
type-check: compose.override.yml
	@docker compose run --rm -w /app -e PYTHONPATH=/app/src django mypy src/scram

## docs-build: build the documentation
.Phony: docs-build
docs-build:
	@docker compose run --rm docs mkdocs build

## docs-serve: build and run a server with the documentation
.Phony: docs-serve
docs-serve:
	@docker compose run --rm docs mkdocs serve -a 0.0.0.0:8888

## copy-libs: copy the translator autogenerated libraries into the translator directory
.Phony: copy-libs
copy-libs:
	@docker compose cp translator:/app/gobgp_pb2.py translator/
	@docker compose cp translator:/app/gobgp_pb2.pyi translator/
	@docker compose cp translator:/app/gobgp_pb2_grpc.py translator/
	@docker compose cp translator:/app/attribute_pb2.py translator/
	@docker compose cp translator:/app/attribute_pb2.pyi translator/
	@docker compose cp translator:/app/attribute_pb2_grpc.py translator/
	@docker compose cp translator:/app/capability_pb2.py translator/
	@docker compose cp translator:/app/capability_pb2.pyi translator/
	@docker compose cp translator:/app/capability_pb2_grpc.py translator/

## update-env-docs: update environment variable documentation append CHECK=true to get a diff if not up to date
.Phony: update-env-docs
update-env-docs:
ifeq ($(CHECK),true)
	@uv run scripts/src/scripts/extract_env_vars.py --check
else
	@uv run scripts/src/scripts/extract_env_vars.py
endif
