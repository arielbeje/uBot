FROM python:3.6

RUN mkdir /code
WORKDIR /code
COPY . .

RUN pip install --upgrade pip \
    && pip install pipenv \
    && pipenv install --skip-lock

ENTRYPOINT ./utils/wait-for-it.sh -h postgres -p 5432 \
           && pipenv run start