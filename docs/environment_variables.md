# Environment Variables Reference

To update, run `make update-env-docs`.

| Variable | Service | Environments | Default | file | Description |
| --- | --- | --- | --- | --- | --- |
| `CELERY_BEAT_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `CELERY_WORKER_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `DEBUG` | Compose | Common | - | [compose.override.local.yml](file://compose.override.local.yml), [compose.override.yml](file://compose.override.yml) | This can be set to either `debugpy` or `pycharm-pydevd` currently |
| `DJANGO_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
| `DOCS_PORT` | Compose | Common | 8888 | [compose.override.local.yml](file://compose.override.local.yml), [compose.override.yml](file://compose.override.yml) | - |
| `FLOWER_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `GOBGP_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
| `GOBGP_VERSION` | Compose | Common | v4.8.0 | [compose.yml](file://compose.yml) | - |
| `HOSTNAME` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `POSTGRES_ENABLED` | Compose | Common | 1 | [compose.override.local.yml](file://compose.override.local.yml), [compose.override.production.yml](file://compose.override.production.yml), [compose.override.yml](file://compose.override.yml), [compose.yml](file://compose.yml) | - |
| `REDIS_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
| `SCRAM_PEERING_IFACE` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V4_ADDRESS` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V4_GATEWAY` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V4_SUBNET` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V6_ADDRESS` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V6_GATEWAY` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `SCRAM_V6_SUBNET` | Compose | Production | - | [compose.override.production.yml](file://compose.override.production.yml) | - |
| `TRANSLATOR_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
| `CONN_MAX_AGE` | Django | Production | 60 | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | noqa F405 |
| `DATABASE_URL` | Django | Common | - | [django/src/config/settings/base.py](file://django/src/config/settings/base.py), [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | DATABASES https docs.djangoproject.com/en/dev/ref/settings databases |
| `DEBUG` | Django | Unknown | - | [django/src/config/asgi.py](file://django/src/config/asgi.py) | Here we setup a debugger if this is desired. This obviously should not be run in production |
| `DJANGO_ADMIN_URL` | Django | Production | - | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | ADMIN Django Admin URL regex |
| `DJANGO_ALLOWED_HOSTS` | Django | Production | ["django"] | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings allowed-hosts |
| `DJANGO_DEFAULT_FROM_EMAIL` | Django | Production | "SCRAM <noreply@es.net>" | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | EMAIL https docs.djangoproject.com/en/dev/ref/settings default-from-email |
| `DJANGO_EMAIL_SUBJECT_PREFIX` | Django | Production | "[SCRAM]" | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings email-subject-prefix |
| `DJANGO_READ_DOT_ENV_FILE` | Django | Common | False | [django/src/config/settings/base.py](file://django/src/config/settings/base.py) | - |
| `DJANGO_SECURE_HSTS_PRELOAD` | Django | Production | True | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings secure-hsts-preload |
| `DJANGO_SECURE_SSL_REDIRECT` | Django | Production | True | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings secure-ssl-redirect |
| `DJANGO_SERVER_EMAIL` | Django | Production | DEFAULT_FROM_EMAIL | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings server-email |
| `DJANGO_SETTINGS_MODULE` | Django | Unknown | "config.settings.local" | [django/src/config/asgi.py](file://django/src/config/asgi.py), [django/src/config/wsgi.py](file://django/src/config/wsgi.py) | If DJANGO_SETTINGS_MODULE is unset, default to the local settings |
| `OIDC_RP_CLIENT_ID` | Django | Common | - | [django/src/config/settings/base.py](file://django/src/config/settings/base.py) | - |
| `OIDC_RP_CLIENT_SECRET` | Django | Common | - | [django/src/config/settings/base.py](file://django/src/config/settings/base.py) | - |
| `POSTGRES_SSL` | Django | Production | True | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | - |
| `REDIS_HOST` | Django | Common | "redis" | [django/src/config/settings/base.py](file://django/src/config/settings/base.py) | - |
| `REDIS_URL` | Django | Production | - | [django/src/config/settings/production.py](file://django/src/config/settings/production.py) | - |
| `SCRAM_AUTH_METHOD` | Django | Common | "local" | [django/src/config/settings/base.py](file://django/src/config/settings/base.py) | Are you using local passwords or oidc? |
| `USE_DOCKER` | Django | Local | "no" | [django/src/config/settings/local.py](file://django/src/config/settings/local.py) | - |
| `DJANGO_SETTINGS_MODULE` | Other | Unknown | "config.settings.local" | [django/src/manage.py](file://django/src/manage.py) | - |
