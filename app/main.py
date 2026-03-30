from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import engine, Base
from .routers import dashboard, partners, inventory, sales, purchases, assets, seed

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Retail ERP Prototype")

app.include_router(dashboard.router)
app.include_router(partners.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(assets.router)
app.include_router(seed.router)