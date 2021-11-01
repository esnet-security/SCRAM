.DEFAULT_GOAL := help

## toggle-prod: configure make to use the production stack
.Phony: toggle-prod
toggle-prod:
	@ln -sf production.yml active.yml

## toggle-local: configure make to use the local stack
.Phony: toggle-local
toggle-local:
	@ln -sf local.yml active.yml

# Since toggle-(local|prod) are phony targets, this file is not tracked
# to compare if its "newer" so running another target with this as a prereq
# will not run this target again. That would overwrite active.yml back to local.yml
# no matter what, which is bad. Phony targets prevents this
## active.yml: creates file active.yml on first run (as a prereq)
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

## behave-translator
.Phony: behave-translator
behave-translator: active.yml
	@docker-compose -f active.yml exec -T redis_to_gobgp_translator behave /app/acceptance/features

## build: rebuilds all your containers
.Phony: build
build: active.yml
	@docker-compose -f active.yml build

## ci-test: runs all tests just like Gitlab CI does
.Phony: ci-test
ci-test: | toggle-local build migrate run pytest behave-all

## cleanup: remove local containers and volumes
.Phony: clean
clean: active.yml
	@docker-compose -f active.yml rm -f -s
	@docker volume prune -f

## collect-static: run collect static admin command
.Phony: collectstatic
collectstatic: active.yml
	@docker-compose -f active.yml run django python manage.py collectstatic

## copy: copy files over to staging server for testing (append STAGING=staging_host_here)
# This is faster than using tower to push things out and it still keeps changes being made locally instead of remote
.Phony: copy
copy:
	rsync -rl ./scram/* $(STAGING):/usr/local/scram/scram/m.

## django-addr: get the IP and ephemeral port assigned to docker:8000
.Phony: django-addr
django-addr: active.yml
	@docker-compose -f active.yml port django 8000

## django-url: get the URL based on http://$(make django-addr)
.Phony: django-url
django-url: active.yml
	@echo http://$$(make django-addr)

## down: turn down docker compose stack
.Phony: down
down: active.yml
	@docker-compose -f active.yml down

## exec: executes a given command on a given container (append CONTAINER=container_name_here and COMMAND=command_here)
.Phony: exec
exec: active.yml
	@docker-compose -f active.yml exec $(CONTAINER) $(COMMAND)

# This automatically builds the help target based on commands prepended with a double hashbang
## help: print this help output
.Phony: help
help: Makefile
	@sed -n 's/^##//p' $<

## tail-log: tail a docker container's logs (append CONTAINER=container_name_here)
.Phony: tail-log
tail-log: active.yml
	@docker-compose -f active.yml logs -f $(CONTAINER)

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
