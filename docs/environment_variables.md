# Environment Variables Reference

To update, run `make update-env-docs`.

| Variable | Service | Environments | Default | file | Description |
| --- | --- | --- | --- | --- | --- |
| `CELERY_BEAT_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `CELERY_WORKER_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `DEBUG` | Compose | Multiple | - | [compose.override.local.yml](file://compose.override.local.yml), [compose.override.yml](file://compose.override.yml) | Here we setup a debugger if this is desired. This obviously should not be run in production |
| `DJANGO_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
| `DOCS_PORT` | Compose | Multiple | 8888 | [compose.override.local.yml](file://compose.override.local.yml), [compose.override.yml](file://compose.override.yml) | - |
| `FLOWER_REPLICAS` | Compose | Common | 0 | [compose.yml](file://compose.yml) | - |
| `GOBGP_REPLICAS` | Compose | Common | 1 | [compose.yml](file://compose.yml) | - |
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
| `CONN_MAX_AGE` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | noqa F405 |
| `DATABASE_URL` | Django | Common | - | [config/settings/base.py](file://config/settings/base.py), [config/settings/production.py](file://config/settings/production.py) | DATABASES https docs.djangoproject.com/en/dev/ref/settings databases |
| `DEBUG` | Django | Unknown | - | [config/asgi.py](file://config/asgi.py) | Here we setup a debugger if this is desired. This obviously should not be run in production |
| `DJANGO_ADMIN_URL` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | ADMIN Django Admin URL regex |
| `DJANGO_ALLOWED_HOSTS` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings allowed-hosts |
| `DJANGO_DEFAULT_FROM_EMAIL` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | EMAIL https docs.djangoproject.com/en/dev/ref/settings default-from-email |
| `DJANGO_EMAIL_BACKEND` | Django | Common | - | [config/settings/base.py](file://config/settings/base.py), [config/settings/local.py](file://config/settings/local.py) | EMAIL https docs.djangoproject.com/en/dev/ref/settings email-backend |
| `DJANGO_EMAIL_SUBJECT_PREFIX` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings email-subject-prefix |
| `DJANGO_READ_DOT_ENV_FILE` | Django | Common | - | [config/settings/base.py](file://config/settings/base.py) | - |
| `DJANGO_SECURE_CONTENT_TYPE_NOSNIFF` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/middleware x-content-type-options-nosniff |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings secure-hsts-include-subdomains |
| `DJANGO_SECURE_HSTS_PRELOAD` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings secure-hsts-preload |
| `DJANGO_SECURE_SSL_REDIRECT` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings secure-ssl-redirect |
| `DJANGO_SERVER_EMAIL` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | https docs.djangoproject.com/en/dev/ref/settings server-email |
| `DJANGO_SETTINGS_MODULE` | Django | Unknown | - | [config/wsgi.py](file://config/wsgi.py) | os.environ DJANGO_SETTINGS_MODULE = "config.settings.production" # noqa ERA001 |
| `OIDC_RP_CLIENT_ID` | Django | Common | - | [config/settings/base.py](file://config/settings/base.py) | - |
| `OIDC_RP_CLIENT_SECRET` | Django | Common | - | [config/settings/base.py](file://config/settings/base.py) | - |
| `POSTGRES_SSL` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | - |
| `REDIS_HOST` | Django | Common | "redis" | [config/settings/base.py](file://config/settings/base.py) | - |
| `REDIS_URL` | Django | Production | - | [config/settings/production.py](file://config/settings/production.py) | - |
| `SCRAM_AUTH_METHOD` | Django | Common | "local" | [config/settings/base.py](file://config/settings/base.py) | Are you using local passwords or oidc? |
| `USE_DOCKER` | Django | Local | - | [config/settings/local.py](file://config/settings/local.py) | - |
| `BAR` | Other | Test | - | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | A useful comment " VAR = os.getenv FOO # Same line comment " VAR2 = os.getenv BAR |
| `DEFAULT_VAR` | Other | Test | 'my_default' | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | Has default |
| `DJANGO_VAR` | Other | Test | - | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | - |
| `ENV_VAR` | Other | Test | "env_def" | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | - |
| `FOO` | Other | Test | - | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | A useful comment " VAR = os.getenv FOO # Same line comment " VAR2 = os.getenv BAR |
| `STANDARD_VAR` | Other | Test | - | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | This is standard |
| `STRICT_VAR` | Other | Test | - | [scripts/tests/test_extract_env_vars.py](file://scripts/tests/test_extract_env_vars.py) | - |
| `CELERY_BROKER_URL` | Scheduler | Test | - | [scheduler/tests/test_settings.py](file://scheduler/tests/test_settings.py) | - |
| `CELERY_RESULT_BACKEND` | Scheduler | Test | - | [scheduler/tests/test_settings.py](file://scheduler/tests/test_settings.py) | - |
| `DISABLE_PROCESS_UPDATES` | Scheduler | Test | - | [scheduler/tests/test_app.py](file://scheduler/tests/test_app.py) | Set the disable env var and then reload settings, then the app |
| `SCRAM_API_URL` | Scheduler | Test | - | [scheduler/tests/test_settings.py](file://scheduler/tests/test_settings.py) | - |
| `DEBUG` | Translator | Unknown | - | [translator/src/translator/translator.py](file://translator/src/translator/translator.py) | Here we setup a debugger if this is desired. This obviously should not be run in production |
| `SCRAM_EVENTS_URL` | Translator | Unknown | "ws://django:8000/ws/route_manager/translator_block/" | [translator/src/translator/translator.py](file://translator/src/translator/translator.py) | - |
| `SCRAM_HOSTNAME` | Translator | Unknown | "scram_hostname_not_set" | [translator/src/translator/translator.py](file://translator/src/translator/translator.py) | Must match the URL in asgi.py, and needs a trailing slash |
