# cloudzoo-issuer

A _starting point_ for a third-party Cloud Zoo issuer

## Getting Started

The steps below will get you up and running on your local machine for development and testing. The instructions are currently macOS-specific. You'll need git and Python 3 pre-installed on your machine.

1. Clone the repository
    ```commandline
    git clone https://github.com/mcneel/cloudzoo-issuer
    cd cloudzoo-issuer
    ```

1. (Optional) Use a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
    ```commandline
    python -m venv venv
    . venv/bin/activate
    pip install -U pip wheel
    ```
    _This allows you to install python packages for this project and only this project_

1. Install python packages
    ```commandline
    pip install -r requirements.txt
    ```
1. Create a .env file (for local use only)
    ```commandline
    cp .env.example .env
    ```
    _This allows you to define environment variables for this project and only this project_

1. Create the initial database
    ```commandline
    flask create-db
    ```

1. Run the app
    ```commandline
    flask run
    ```

1. In another terminal, test the endpoints
    ```commandline
    curl http://localhost:5000/info
    ```
    ```text
    You have 3 licenses!
    ```

## Troubleshooting

Flask's default port (5000) is [used by AirPlay Receiver in macOS Monterey](https://stackoverflow.com/a/69829313). Either turn it off, or choose a different port (e.g. `flask run -p 5001`).

## Deploy

### Heroku

The recommended option. Super easy!

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

<!-- TODO: create db -->

### Docker

```commandline
docker-compose up -d
docker-compose exec web flask create-db

docker-compose logs -f
```
