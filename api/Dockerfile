FROM python:3.12.12-slim

RUN apt-get update && apt-get install --yes --no-install-recommends make

WORKDIR /app
COPY makefile .

COPY pyproject.toml .
COPY uv.lock .
RUN make install

COPY . .

EXPOSE 5000
CMD ["make", "start-prod"]
