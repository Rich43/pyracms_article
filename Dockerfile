FROM python:latest

# We copy this file first to leverage docker cache
COPY ./requirements.txt /code/article/requirements.txt

WORKDIR /code/article

RUN pip install -r requirements.txt

COPY . /code/article

RUN python setup.py bdist_wheel

