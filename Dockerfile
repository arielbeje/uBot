FROM python:3.9

WORKDIR /code
COPY . .

RUN pip install .

ENTRYPOINT python main.py
