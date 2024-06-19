FROM python:alpine


RUN pip install poetry

COPY . .

RUN poetry install

ENTRYPOINT ["poetry", "run", "python", "-m", "manage", "--host='0.0.0.0'", "--port=443", "--ssl_context='adhoc'"]




