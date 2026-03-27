from fastapi import FastAPI
from .db import Base, engine
from .routers import dashboard, inventory, partners, sales, purchases, finance, assets

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Department Store ERP Prototype")

app.include_router(dashboard.router)
app.include_router(inventory.router)
app.include_router(partners.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(finance.router)
app.include_router(assets.router)


@app.get("/health")
def health():
    return {"status": "ok"}