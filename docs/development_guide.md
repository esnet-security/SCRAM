## Technology Explainer

This project is based off of [this cookiecutter](https://github.com/cookiecutter/cookiecutter-django), which is based off of the book [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x). This book provides an opinionated take on Django. If you are working on this project, and stuck on the "how" for a given situation, your first step should be to see if the book has a suggestion.

SCRAM utilizes `docker compose` to run the following stack in production:
* nginx (as a webserver and static asset server)
* django (web framework)
* postgres (database)
* gobgp (communicating with networking gear for actions; blocking, shunting, redirecting, etc)
* translator (a tool to pull information from SCRAM via websockets and send to gobgp container over gRPC)

The last two could theoretically be pulled out and run separately from the rest of this stack, but for the time being, we are running them all on the same host(s).

### Styling

We strive to follow [pep8](https://peps.python.org/pep-0008/) in almost all cases. See setup.cfg for the instances in which we differ.

### Working with Git

We use git as our VCS and the main repo is stored on ESnet's [gitlab instance](https://gitlab.es.net/security/scram). We utilize a git-flow branching strategy on this project. For more information on what this means, please see [this reference](https://www.gitkraken.com/learn/git/git-flow).

## Expected Development Patterns

Changes are expected to be created and tested fully locally using docker. This should give a higher level of confidence in changes, as well as speed up the development cycle as you can immediately test things locally. Theoretically we can run either the local or production version (no SSL) on our development workstations. Production will mirror that of a true production instance (minus SSL), whereas local runs with more debugging options and no web server since the dev version of django can serve all we need.

Accepted branch naming examples:
* `topic/soehlert/add_docs-sec-123` (the sec-123 represents a jira ticket number)
* `topic/soehlert/update_docs` (if there is no related jira ticket)
* `hotfix/broken_thing`

1. Clone this repo
2. Branch off of the appropriate protected branch (likely develop)
   1. `git checkout develop`
   2. `git checkout -b topic/$name/$feature`
3. Run migrations (MUST DO FIRST TIME) `make migrate`
4. Choose if you want local or prod `make toggle-local` or `make toggle-prod`
5. Build the stack if you haven't before (or you've done a clean) `make build`
6. Run the stack `make run`
7. Open the site `make django-open`
8. Make your changes and it should auto reload
9. Make sure to add or update tests

## Testing

We should be testing as much as we reasonably can. Currently, there is a mix of (behave-django)[https://behave-django.readthedocs.io/en/stable/] and pytest. If you are unsure which of the two to use, please feel free to ask.

* To run all behave tests `make behave-all`
* To run a specific set of behave tests `make behave FEATURE=$feature-name`
* To run behave tests on translator `make behave-translator`
* To run pytests `make pytest`
* To run all tests you would have in gitlabCI `make ci-test`

Ideally we would never have failing tests getting merged, so clearing up the `make ci-test` before a merge request is suggested.

#### Debugging Tests

If you are seeing failed API calls, you can try to browse the API directly in a web browser. You can also try to run some curl commands.

* Use curl with basic auth and json content type header 
   1. Make sure you know the admin user password for basic auth `make pass-reset`
   2. Get the correct port `make django-url`
   3. Replace with the correct port `curl -XPOST --user admin:password http://0.0.0.0:62410/api/v1/entrys/ -H 'Content-Type: application/json' --data '{"route": "1.1.1.1/32", "actiontype": "block"}'; echo`

Trying to write test output to a file is a challenge due to running in ephemeral docker containers, but you should be able to print to stderr to get some debug info as needed as well.

## Troubleshooting

There are a few troubleshooting tricks available to you.

* Run with `make toggle-local` as this will turn on debug mode in django
* To see if your blocks are making it into gobgp you can run `make list-routes`
* If you want container logs `make tail-log CONTAINER=$service-name`




