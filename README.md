# python-project-template

## Setup



- `python -m venv <venv-name>` or `path\to\specific\python\interpreter -m venv <venv_name>`
- \<venv-name\Scripts\activate
- `pip install -r requirements.txt`

## Install the package as a script

Update the setup.py for this to work properly

`pip install .`

## Run Tests

`cd tests/ && python test_run.py`

## Docker

- `docker build --tag python-template-tag .`
- check it with `docker images`
- `docker run python-template-tag`
