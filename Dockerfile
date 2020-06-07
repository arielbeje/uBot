FROM python:3.7

ARG TOKEN
ENV UBOT=${TOKEN}

WORKDIR /code
COPY . .

RUN pip install .

ENTRYPOINT python main.py
