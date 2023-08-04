# PhoenixAPI 1.0

## Disclaimer

You are yourself responsible for performing the steps neccecary to secure the code from unwanted attackers or data leakage, be it removal of the debug toolbar, or replacing the current signed cookie system.

By using this package, you agree to perform an audit on the code yourself, and to fix any possible issues before using it live

## Setting up

You need to have the following environment variables defined:

```
JWT_SECRET

VIPPS_CLIENT_ID
VIPPS_CLIENT_SECRET
VIPPS_SUBSCRIPTION_KEY
VIPPS_CALLBACK_URL
VIPPS_MERCHANT_SERIAL_NUMBER
```

## Starting the server

The server is made to run under docker. Simply run `docker-compose up` from the root directory. If you want to run specific commands against the container, use `docker-compose run web <command>`. This is useful for running tests etc. If you for some reason want to avoid docker, or if you want to port it to another containerization system, simply use `docker-compose.yml` and `Dockerfile` as documentation as to how the server is set up.

## Steps to develop your own stuff

New pyramid views goes in `views.py`, and are registered in `__init__.py`. Pyramid allows you to do all kinds of cool stuff, so be sure to check the documentation.

In order to create alembic migrations(needed for the actual database to be updated when you change a model), run `docker-compose run rest alembic revision --autogenerate -m "Revision name"`. This will auto-detect changes. Be sure to look over what changes were detected before actually applying it.

## Relevant documentation

### Pyramid

-   Most of the stuff i have written is based on this [Quick tutorial for Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/latest/quick_tutorial/index.html)

### Using alembic

-   See http://alembic.zzzcomputing.com/en/latest/tutorial.html
-   See http://alembic.zzzcomputing.com/en/latest/autogenerate.html for autogeneration
