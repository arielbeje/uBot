FROM python:3.11

WORKDIR /code
COPY . .

# Installing with poetry to utilize poetry.lock
RUN pip install poetry
RUN poetry install

ENTRYPOINT poetry run python main.py
