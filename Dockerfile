FROM python:3.6

RUN mkdir /code
WORKDIR /code
COPY . .

RUN pip install --upgrade pip \
    && pip install pipenv \
    && pipenv install --skip-lock \
    && apt-get install -y curl

ENTRYPOINT curl https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh | bash -s -h postgres -p 5432 \
           && pipenv run start