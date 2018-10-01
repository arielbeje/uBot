FROM python:3.6

RUN mkdir /code
WORKDIR /code
COPY . .

RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --skip-lock
