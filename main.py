from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, SessionLocal, Base
from app.models import *
from app.routers import auth, superadmin, admin, sales, webhook
from app.services.auth_service import hash_password
import os

app = FastAPI(title="Legacy Hub CRM")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(superadmin.router)
app.include_router(admin.router)
app.include_router(sales.router)
app.include_router(webhook.router)

@app.on_event("startup")
def startup():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed superadmin
        from app.models.user import User, RoleEnum
        existing = db.query(User).filter(User.username == "superadmin").first()
        if not existing:
            sa = User(
                name="Super Admin",
                role=RoleEnum.superadmin,
                username="superadmin",
                password_hash=hash_password("admin123")
            )
            db.add(sa)
            db.commit()

        # Seed default sources
        from app.models.source_status import Source, Status
        default_sources = ["Website", "WhatsApp", "Meta", "Referral", "Walk-in", "Phone", "Email"]
        for s in default_sources:
            exists = db.query(Source).filter(Source.name == s).first()
            if not exists:
                db.add(Source(name=s))

        # Seed default statuses
        default_statuses = ["New", "Contacted", "Interested", "Not Interested", "Follow Up", "Converted", "Lost"]
        for s in default_statuses:
            exists = db.query(Status).filter(Status.name == s).first()
            if not exists:
                db.add(Status(name=s))

        db.commit()
    finally:
        db.close()

@app.get("/")
def root():
    return RedirectResponse("/login")
