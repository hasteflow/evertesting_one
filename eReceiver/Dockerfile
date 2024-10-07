FROM pfeiffermax/uvicorn-poetry:3.3.0-python3.12.2-bookworm AS ereceiver


WORKDIR /usr/app

COPY pyproject.toml poetry.lock ./src/** ./
RUN poetry install

EXPOSE 8000
CMD [ "poetry", "run", "python", "./main.py" ]
