from fastapi import FastAPI
from app.api.routes import user
from app.core.database import engine
from sqlalchemy import text
from app.api.routes import org
from app.api.routes import cluster

app = FastAPI()
app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(org.router, prefix="/api/orgs", tags=["Orgs"])
app.include_router(cluster.router, prefix="/api/clusters", tags=["Clusters"])

@app.get("/")
def read_root():
    return {"message": "App is running fine!"}

@app.get("/health/db")
def check_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db": "connected"}
    except Exception as e:
        return {"db": "error", "details": str(e)}
