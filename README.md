# cloudzoo-issuer

A starting point for a third-party Cloud Zoo issuer

## Getting Started

The steps below will get you up and running on your local machine for development and testing. The instructions are currently macOS-specific. You'll need `git`, Python 3, `pip` and `virtualenv` pre-installed on your machine.

1. Clone the repository
    ```commandline
    $ git clone https://github.com/mcneel/cloudzoo-issuer
    $ cd cloudzoo-issuer
    ```

1. (Optional) Create a virtual environment
    ```commandline
    $ virtualenv venv
    ```
    _This allows you to install python packages for this project and only this project_

1. (Optional) Activate the virtual environment
    ```commandline
    $ . venv/bin/activate
    ```
1. Install python packages
    ```commandline
    pip3 install -r requirements.txt
    ```
1. Create a .env file
    ```commandline
    $ cp .env.example .env
    ```
    _This allows you to define environment variables for this project and only this project_

1. Create the initial database
    ```commandline
    $ python3

    >>> from app import db
    >>> db.create_all()
    ```

1. Run the app
    ```commandline
    flask run
    ```

1. In another terminal, test the endpoints
    ```commandline
    $ curl localhost:5000/info

    You have 0 licenses!
    ```
