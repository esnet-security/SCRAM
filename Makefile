# It'd be nice to keep these in sync with the defaults of the Dockerfiles
PYTHON_IMAGE_VER ?= 3.12
POSTGRES_IMAGE_VER ?= 18

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
	@docker compose run --rm django coverage run -a manage.py behave --no-input --simple

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave: compose.override.yml
	@docker compose run --rm django python manage.py behave --no-input --simple -i $(FEATURE)

## integration-tests: runs multi-instance system tests against docker compose running containers
.Phony: integration-tests
integration-tests: run
	@docker compose exec -T django coverage run -a manage.py behave --no-input --use-existing-database scram/route_manager/tests/integration

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

## coverage.xml: generate coverage from test runs
coverage.xml: pytest behave-all integration-tests behave-translator
	@docker compose run --rm django coverage report
	@docker compose run --rm django coverage xml

## ci-test: runs all tests just like Github CI does
.Phony: ci-test
ci-test: | toggle-local build migrate run coverage.xml

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
	@docker compose run --rm django coverage run -m pytest

## pytest-scheduler: runs scheduler package tests with coverage
.Phony: pytest-scheduler
pytest-scheduler:
	@cd scheduler && uv run pytest

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
	@docker compose run --rm django mypy scram

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
