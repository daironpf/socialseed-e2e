#!/usr/bin/env python3
"""
Demo Notifications/Push API for socialseed-e2e Testing

FastAPI-based notifications API with SQLite database.
Use this API to test notification and webhook flows.

Usage:
    pip install fastapi uvicorn sqlalchemy
    
    # Start the API server
    python api-notifications-demo.py
    
    # The API will be available at http://localhost:5007

Endpoints:
    GET    /health                         - Health check
    GET    /api/channels                  - List notification channels
    POST   /api/notifications             - Send notification
    GET    /api/notifications             - List notifications
    GET    /api/notifications/{id}       - Get notification status
    POST   /api/templates                - Create template
    GET    /api/templates                - List templates
    GET    /api/templates/{id}          - Get template
    POST   /api/webhooks                 - Register webhook
    GET    /api/webhooks                 - List webhooks
    POST   /api/webhooks/{id}/test       - Test webhook
    DELETE /api/webhooks/{id}            - Delete webhook
    POST   /api/scheduled                - Schedule notification
    GET    /api/scheduled               - List scheduled
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
import json

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, Column, String, Integer, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import sessionmaker, Session, declarative_base

DATABASE_URL = "sqlite:///./notifications_demo.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class NotificationDB(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    template_id = Column(String, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="normal")
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TemplateDB(Base):
    __tablename__ = "templates"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    subject_template = Column(String, nullable=True)
    body_template = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WebhookDB(Base):
    __tablename__ = "webhooks"
    id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)
    secret = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ScheduledDB(Base):
    __tablename__ = "scheduled"
    id = Column(String, primary_key=True, index=True)
    notification_id = Column(String, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    channel: str
    subject: Optional[str] = None
    body: str
    template_id: Optional[str] = None
    status: str
    priority: str
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    metadata: Optional[dict] = None
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: str
    channel: str = Field(default="email")
    subject: Optional[str] = None
    body: str
    template_id: Optional[str] = None
    priority: str = Field(default="normal")
    scheduled_at: Optional[str] = None
    metadata: Optional[dict] = None


class TemplateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    channel: str
    subject_template: Optional[str] = None
    body_template: str
    variables: Optional[dict] = None
    is_active: bool
    created_at: datetime


class TemplateCreate(BaseModel):
    name: str
    channel: str
    subject_template: Optional[str] = None
    body_template: str
    variables: Optional[dict] = None


class WebhookSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    url: str
    events: list[str]
    secret: str
    is_active: bool
    created_at: datetime


class WebhookCreate(BaseModel):
    url: str
    events: list[str]


app = FastAPI(title="Notifications Demo API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database(db: Session):
    if db.query(TemplateDB).first():
        return
    
    templates = [
        TemplateDB(id="tpl_1", name="welcome", channel="email", subject_template="Welcome {{name}}!", body_template="Hello {{name}}, welcome to our service!", variables={"name": "string"}),
        TemplateDB(id="tpl_2", name="order_confirmation", channel="email", subject_template="Order Confirmed", body_template="Your order #{{order_id}} has been confirmed.", variables={"order_id": "string"}),
        TemplateDB(id="tpl_3", name="password_reset", channel="email", subject_template="Reset Password", body_template="Click here to reset: {{reset_link}}", variables={"reset_link": "string"}),
    ]
    db.add_all(templates)
    
    webhooks = [
        WebhookDB(id="wh_1", url="https://example.com/webhook", events=["notification.sent", "notification.delivered"], secret="secret123"),
    ]
    db.add_all(webhooks)
    db.commit()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "notifications-demo", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/channels")
def list_channels():
    return {"channels": ["email", "sms", "push", "webhook"]}


@app.post("/api/notifications", response_model=NotificationSchema)
def send_notification(notif: NotificationCreate, db: Session = Depends(get_db)):
    scheduled_at = None
    if notif.scheduled_at:
        try:
            scheduled_at = datetime.fromisoformat(notif.scheduled_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled_at format")
    
    import random
    statuses = ["sent", "delivered", "pending"]
    status = random.choice(statuses) if not scheduled_at else "scheduled"
    
    notif_id = f"notif_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    
    db_notif = NotificationDB(
        id=notif_id,
        user_id=notif.user_id,
        channel=notif.channel,
        subject=notif.subject,
        body=notif.body,
        template_id=notif.template_id,
        status=status,
        priority=notif.priority,
        scheduled_at=scheduled_at,
        sent_at=now if status != "pending" else None,
        delivered_at=now if status == "delivered" else None,
        metadata_json=notif.metadata_json
    )
    db.add(db_notif)
    
    if scheduled_at:
        db_sched = ScheduledDB(id=f"sched_{uuid.uuid4().hex[:8]}", notification_id=notif_id, scheduled_for=scheduled_at)
        db.add(db_sched)
    
    db.commit()
    db.refresh(db_notif)
    return db_notif


@app.get("/api/notifications", response_model=list[NotificationSchema])
def list_notifications(user_id: str = Query(...), status: Optional[str] = None, channel: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(NotificationDB).filter(NotificationDB.user_id == user_id)
    if status:
        query = query.filter(NotificationDB.status == status)
    if channel:
        query = query.filter(NotificationDB.channel == channel)
    return query.order_by(NotificationDB.created_at.desc()).all()


@app.get("/api/notifications/{notification_id}", response_model=NotificationSchema)
def get_notification(notification_id: str, db: Session = Depends(get_db)):
    notif = db.query(NotificationDB).filter(NotificationDB.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@app.post("/api/templates", response_model=TemplateSchema)
def create_template(tpl: TemplateCreate, db: Session = Depends(get_db)):
    tpl_id = f"tpl_{uuid.uuid4().hex[:8]}"
    db_tpl = TemplateDB(id=tpl_id, **tpl.model_dump())
    db.add(db_tpl)
    db.commit()
    db.refresh(db_tpl)
    return db_tpl


@app.get("/api/templates", response_model=list[TemplateSchema])
def list_templates(db: Session = Depends(get_db)):
    return db.query(TemplateDB).filter(TemplateDB.is_active == True).all()


@app.get("/api/templates/{template_id}", response_model=TemplateSchema)
def get_template(template_id: str, db: Session = Depends(get_db)):
    tpl = db.query(TemplateDB).filter(TemplateDB.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@app.post("/api/webhooks", response_model=WebhookSchema)
def create_webhook(wh: WebhookCreate, db: Session = Depends(get_db)):
    wh_id = f"wh_{uuid.uuid4().hex[:8]}"
    secret = uuid.uuid4().hex
    db_wh = WebhookDB(id=wh_id, url=wh.url, events=wh.events, secret=secret)
    db.add(db_wh)
    db.commit()
    db.refresh(db_wh)
    return db_wh


@app.get("/api/webhooks", response_model=list[WebhookSchema])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(WebhookDB).filter(WebhookDB.is_active == True).all()


@app.post("/api/webhooks/{webhook_id}/test")
def test_webhook(webhook_id: str, db: Session = Depends(get_db)):
    wh = db.query(WebhookDB).filter(WebhookDB.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Test webhook triggered", "url": wh.url, "status": "success"}


@app.delete("/api/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str, db: Session = Depends(get_db)):
    wh = db.query(WebhookDB).filter(WebhookDB.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    wh.is_active = False
    db.commit()
    return {"message": "Webhook deleted"}


@app.get("/api/scheduled")
def list_scheduled(user_id: str = Query(...), db: Session = Depends(get_db)):
    notifs = db.query(NotificationDB).filter(
        NotificationDB.user_id == user_id,
        NotificationDB.status == "scheduled"
    ).all()
    return notifs


if __name__ == "__main__":
    import uvicorn
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    
    print("=" * 60)
    print("🚀 Notifications Demo API for socialseed-e2e Testing")
    print("=" * 60)
    print("\n📍 API URL: http://localhost:5007")
    print("\nChannels: email, sms, push, webhook")
    print("\nAvailable endpoints:")
    print("  GET    /health                    - Health")
    print("  GET    /api/channels              - List channels")
    print("  POST   /api/notifications         - Send notification")
    print("  GET    /api/notifications         - List notifications")
    print("  GET    /api/notifications/{id}    - Get notification")
    print("  POST   /api/templates            - Create template")
    print("  GET    /api/templates            - List templates")
    print("  POST   /api/webhooks             - Register webhook")
    print("  GET    /api/webhooks             - List webhooks")
    print("  POST   /api/webhooks/{id}/test   - Test webhook")
    print("\nPress Ctrl+C")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5007)
