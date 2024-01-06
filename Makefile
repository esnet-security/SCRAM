.DEFAULT_GOAL := help

## toggle-prod: configure make to use the production stack
.Phony: toggle-prod
toggle-prod:
	@ln -sf production.yml docker-compose.yaml

## toggle-local: configure make to use the local stack
.Phony: toggle-local
toggle-local:
	@ln -sf local.yml docker-compose.yaml

# Since toggle-(local|prod) are phony targets, this file is not tracked
# to compare if its "newer" so running another target with this as a prereq
# will not run this target again. That would overwrite docker-compose.yaml back to local.yml
# no matter what, which is bad. Phony targets prevents this
## docker-compose.yaml: creates file docker-compose.yaml on first run (as a prereq)
docker-compose.yaml:
	@ln -sf local.yml docker-compose.yaml

## behave-all: runs behave inside the containers against all of your features
.Phony: behave-all
behave-all: docker-compose.yaml
	@docker compose run django coverage run -a manage.py behave --no-input --simple

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave: docker-compose.yaml
	@docker compose run django python manage.py behave --no-input --simple -i $(FEATURE)

## behave-translator
.Phony: behave-translator
behave-translator: docker-compose.yaml
	@docker compose exec -T translator /usr/local/bin/behave /app/acceptance/features

## build: rebuilds all your containers or a single one if CONTAINER is specified
.Phony: build
build: docker-compose.yaml
	@docker compose up -d --no-deps --build $(CONTAINER)
	@docker compose restart $(CONTAINER)

## coverage.xml: generate coverage from test runs
coverage.xml: pytest behave-all behave-translator
	@docker compose run django coverage report
	@docker compose run django coverage xml

## ci-test: runs all tests just like Gitlab CI does
.Phony: ci-test
ci-test: | toggle-local build migrate run coverage.xml

## cleanup: remove local containers and volumes
.Phony: clean
clean: docker-compose.yaml
	@docker compose rm -f -s
	@docker volume prune -f

## collect-static: run collect static admin command
.Phony: collectstatic
collectstatic: docker-compose.yaml
	@docker compose run django python manage.py collectstatic

## django-addr: get the IP and ephemeral port assigned to docker:8000
.Phony: django-addr
django-addr: docker-compose.yaml
	@docker compose port django 8000

## django-url: get the URL based on http://$(make django-addr)
.Phony: django-url
django-url: docker-compose.yaml
	@echo http://$$(make django-addr)

## django-open: open a browser for http://$(make django-addr)
.Phony: django-open
django-open: docker-compose.yaml
	@open http://$$(make django-addr)

## down: turn down docker compose stack
.Phony: down
down: docker-compose.yaml
	@docker compose down

## exec: executes a given command on a given container (append CONTAINER=container_name_here and COMMAND=command_here)
.Phony: exec
exec: docker-compose.yaml
	@docker compose exec $(CONTAINER) $(COMMAND)

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

# TODO: When we move to flowspec this -a flag with change
## list-routes: list gobgp routes
.Phony: list-routes
list-routes: docker-compose.yaml
	@docker compose exec gobgp gobgp global rib -a ipv4
	@docker compose exec gobgp gobgp global rib -a ipv6

## migrate: makemigrations and then migrate
.Phony: migrate
migrate: docker-compose.yaml
	@docker compose run django ls
	@docker compose run django python manage.py makemigrations
	@docker compose run django python manage.py migrate

## pass-reset: change admin's password
.Phony: pass-reset
pass-reset: docker-compose.yaml
	@docker compose run django python manage.py changepassword admin

## pytest: runs pytest inside the containers
.Phony: pytest
pytest: docker-compose.yaml
	@docker compose run django coverage run -m pytest

## run: brings up the containers as described in docker-compose.yaml
.Phony: run
run: docker-compose.yaml
	@docker compose up -d

## stop: turns off running containers
.Phony: stop
stop: docker-compose.yaml
	@docker compose stop

## tail-log: tail a docker container's logs (append CONTAINER=container_name_here)
.Phony: tail-log
tail-log: docker-compose.yaml
	@docker compose logs -f $(CONTAINER)

## type-check: static type checking
.Phony: type-check
type-check: docker-compose.yaml
	@docker compose run django mypy scram
