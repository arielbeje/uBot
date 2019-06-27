FROM python:3.7

ARG TOKEN
ENV UBOT=${TOKEN}

RUN mkdir /code
WORKDIR /code
COPY . .

RUN pip install --upgrade pip \
    && pip install .

ENTRYPOINT python main.py
