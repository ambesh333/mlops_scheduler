#!/bin/bash

docker run --name mlops_postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=mlops \
  -p 5432:5432 \
  -d postgres


python -m app.core.run_deployments


alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

uvicorn app.main:app --reload

docker exec -it mlops_postgres psql -U user -d mlops
