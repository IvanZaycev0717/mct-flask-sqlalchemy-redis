FROM python:alpine

RUN pip install poetry==1.8.2

ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true

RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}

COPY . ./

RUN poetry install --without dev

RUN chmod u+x start_app.sh

EXPOSE 443


ENTRYPOINT ["poetry", "run", "./start_app.sh"]



