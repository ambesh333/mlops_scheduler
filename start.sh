#!/bin/bash

docker run --name mlops_postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=mlops \
  -p 5432:5432 \
  -d postgres


alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
