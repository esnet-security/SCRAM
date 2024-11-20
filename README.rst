SCRAM
=====

Security Catch and Release Automation Manager

.. image:: https://coveralls.io/repos/github/esnet-security/SCRAM/badge.svg
     :target: https://coveralls.io/github/esnet-security/SCRAM
     :alt: Coveralls Code Coverage Stats
.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style

:License: BSD

====

Overview
====

SCRAM is a web based service to assist in automation of security data. There is a web interface as well as a REST API available.
The idea is to create actiontypes which allow you to take actions on the IPs/cidr networks you provide.

Components
====
SCRAM utilizes ``docker compose`` to run the following stack in production:

- nginx (as a webserver and static asset server)
- django (web framework)
- postgres (database)
- redis (backs django channel layers)
- gobgp (communicating with networking gear over bgp for actions; blocking, shunting, redirecting, etc)
- translator (a tool to pull information from SCRAM via websockets and send to gobgp container over gRPC)

A predefined actiontype of "block" exists which utilizes bgp nullrouting to effectivley block any traffic you want to apply.
You can add any other actiontypes via the admin page of the web interface dynamically, but keep in mind translator support would need to be added as well.

Installation
====

To get a basic implementation up and running locally:

- Pull this repository to start: ``git clone``
- ``cd scram``
- Create ``$scram_home/.envs/.production/.django`` a template exists in the docs/templates directory
    - Make sure to update all the settings in the file
    - Remove the OIDC parts if you do not want to use OIDC
- Create ``$scram_home/.envs/.production/.postgres`` a template exists in the docs/templates directory
    - Make sure to set the right credentials
    - By default this template assumes you have a service defined in docker compose file called postgres. If you use another postgres server, make sure to update that setting as well
- Create a ``.env`` file with the necessary environment variables:
    - [comment]: # This chooses if you want to use oidc or local accounts. This can be local or oidc only. Default: `local`
    - scram_auth_method: "local"
- ``make build``
- ``make toggle-prod``
    - This will turn off debug mode in django and start using nginx to reverse proxy for the app
        - you should add some certs as well and pass them into the nginx container
- ``make run``
- ``make django-open``


*** Copyright Notice ***
====

Security Catch and Release Automation Manager (SCRAM) Copyright (c) 2022,
The Regents of the University of California, through Lawrence Berkeley
National Laboratory (subject to receipt of any required approvals from the
U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative
works, and perform publicly and display publicly, and to permit others to do so.
