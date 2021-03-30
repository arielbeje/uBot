FROM python:3.9

ARG TOKEN
ENV UBOT=${TOKEN}

WORKDIR /code
COPY . .

RUN pip install .

ENTRYPOINT python main.py
