.DEFAULT_GOAL := help

## toggle-prod: configure make to use the production stack
.Phony: toggle-prod
toggle-prod:
	@ln -sf production.yml compose.yaml

## toggle-local: configure make to use the local stack
.Phony: toggle-local
toggle-local:
	@ln -sf local.yml compose.yaml

# Since toggle-(local|prod) are phony targets, this file is not tracked
# to compare if its "newer" so running another target with this as a prereq
# will not run this target again. That would overwrite compose.yaml back to local.yml
# no matter what, which is bad. Phony targets prevents this
## compose.yaml: creates file compose.yaml on first run (as a prereq)
compose.yaml:
	@ln -sf local.yml compose.yaml

## behave-all: runs behave inside the containers against all of your features
.Phony: behave-all
behave-all: compose.yaml
	@docker-compose run django coverage run -a manage.py behave --no-input --simple

## behave: runs behave inside the containers against a specific feature (append FEATURE=feature_name_here)
.Phony: behave
behave: compose.yaml
	@docker-compose run django python manage.py behave --no-input --simple -i $(FEATURE)

## behave-translator
.Phony: behave-translator
behave-translator: compose.yaml
	@docker-compose exec -T redis_to_gobgp_translator /usr/local/bin/behave /app/acceptance/features

## build: rebuilds all your containers or a single one if CONTAINER is specified
.Phony: build
build: compose.yaml
	@docker-compose up -d --no-deps --build $(CONTAINER)
	@docker-compose restart $(CONTAINER)

## coverage.xml: generate coverage from test runs
coverage.xml: pytest behave-all behave-translator
	@docker-compose run django coverage report
	@docker-compose run django coverage xml

## ci-test: runs all tests just like Gitlab CI does
.Phony: ci-test
ci-test: | toggle-local build migrate run coverage.xml

## cleanup: remove local containers and volumes
.Phony: clean
clean: compose.yaml
	@docker-compose rm -f -s
	@docker volume prune -f

## collect-static: run collect static admin command
.Phony: collectstatic
collectstatic: compose.yaml
	@docker-compose run django python manage.py collectstatic

## copy: copy files over to staging server for testing (append STAGING=staging_host_here)
# This is faster than using tower to push things out and it still keeps changes being made locally instead of remote
.Phony: copy
copy:
	rsync -rl ./scram/* $(STAGING):/usr/local/scram/scram/m.

## django-addr: get the IP and ephemeral port assigned to docker:8000
.Phony: django-addr
django-addr: compose.yaml
	@docker-compose port django 8000

## django-url: get the URL based on http://$(make django-addr)
.Phony: django-url
django-url: compose.yaml
	@echo http://$$(make django-addr)

## django-open: open a browser for http://$(make django-addr)
.Phony: django-open
django-open: compose.yaml
	@open http://$$(make django-addr)

## down: turn down docker compose stack
.Phony: down
down: compose.yaml
	@docker-compose down

## exec: executes a given command on a given container (append CONTAINER=container_name_here and COMMAND=command_here)
.Phony: exec
exec: compose.yaml
	@docker-compose exec $(CONTAINER) $(COMMAND)

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

## list-routes: list gobgp routes
.Phony: list-routes
list-routes: compose.yaml
	@docker-compose exec gobgp gobgp global rib


## tail-log: tail a docker container's logs (append CONTAINER=container_name_here)
.Phony: tail-log
tail-log: compose.yaml
	@docker-compose logs -f $(CONTAINER)

## migrate: makemigrations and then migrate
.Phony: migrate
migrate: compose.yaml
	@docker-compose run django python manage.py makemigrations
	@docker-compose run django python manage.py migrate

## pytest: runs pytest inside the containers
.Phony: pytest
pytest: compose.yaml
	@docker-compose run django coverage run -m pytest

## run: brings up the containers as described in compose.yaml
.Phony: run
run: compose.yaml
	@docker-compose up -d

## stop: turns off running containers
.Phony: stop
stop: compose.yaml
	@docker-compose stop

## type-check: static type checking
.Phony: type-check
type-check: compose.yaml
	@docker-compose run django mypy scram

## pass-reset: change admin's password
.Phony: pass-reset
pass-reset: compose.yaml
	@docker-compose run django python manage.py changepassword admin
