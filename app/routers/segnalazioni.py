import re
import os
import requests
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.schemas.emaildata import EmailData, EmailDataCreate, EmailDataUpdate, EmailDataPublic, SegnalazioneOut, SegnalazioneStatusUpdate
from app.auth.dependencies import get_current_user

from app.middlewares.rate_limiter import RateLimiterMiddleware

from app.logging_config import setup_logging
from datetime import datetime
from typing import List, Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from datetime import timedelta
from sqlalchemy import func
from urllib.parse import urlparse

# -----------------------------
# COSTANTI GLOBALI
# -----------------------------

FLASK_DELETE_ENDPOINT = "https://ws.citylog.cloud/upload/delete"  # Cambia con URL corretto server Flask
#FLASK_DELETE_ENDPOINT = "http://192.168.1.43:9000/upload/delete"  # Cambia con URL corretto server Flask

router = APIRouter(prefix="/segnalazioni", tags=["Segnalazioni"])

# Inizializza il logger
logger = setup_logging()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[SegnalazioneOut])
def get_my_segnalazioni(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get('id') or current_user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    segnalazioni = (
        db.query(EmailDataModel)
        .filter(EmailDataModel.user_id == user_id)
        .order_by(EmailDataModel.image_time.desc())
        .all()
    )
    return segnalazioni

@router.get("/{id}", response_model=EmailData)
async def get_segnalazione(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(
        UserModel.email == current_user["email"]
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utente non trovato"
        )

    record = db.query(EmailDataModel).filter(
        EmailDataModel.id == id,
        EmailDataModel.user_id == db_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segnalazione non trovata"
        )

    return record

@router.delete("/{id}")
async def delete_segnalazione(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user_id = int(current_user["sub"])

    db_item = db.query(EmailDataModel).filter(
        EmailDataModel.id == id,
        EmailDataModel.user_id == user_id
    ).first()

    if not db_item:
        raise HTTPException(
            status_code=404,
            detail="Segnalazione non trovata"
        )

    db.delete(db_item)
    db.commit()

    return {"message": "Segnalazione eliminata"}

@router.put("/{id}")
async def update_segnalazione_status(
    id: int = Path(..., description="ID della segnalazione"),
    status_update: SegnalazioneStatusUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logger.info(f"CURRENT USER: {current_user}")
    logger.info(f"STATUS UPDATE: {status_update}")

    user_id = int(current_user["sub"])

    db_item = db.query(EmailDataModel).filter(
        EmailDataModel.id == id,
        EmailDataModel.user_id == user_id
    ).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segnalazione non trovata o non autorizzata"
        )

    db_item.status = status_update.status

    db.commit()
    db.refresh(db_item)

    logger.info(
        f"Segnalazione {id} aggiornata a status {status_update.status} da utente {user_id}"
    )

    return db_item

@router.put("/{id__}")
async def update_segnalazione_status(
    id: int,
    status_update: SegnalazioneStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    logger.info(f"CURRENT USER: {current_user}")
    logger.info(f"STATUS UPDATE: {status_update}")

    # recupero user_id dal token JWT
    user_id = int(current_user["sub"])

    # recupero segnalazione solo se appartiene all'utente
    db_item = db.query(EmailDataModel).filter(
        EmailDataModel.id == id,
        EmailDataModel.user_id == user_id
    ).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Segnalazione non trovata o non autorizzata"
        )

    # aggiornamento status
    db_item.status = status_update.status

    db.commit()
    db.refresh(db_item)

    logger.info(f"Segnalazione {id} aggiornata a status {status_update.status} da utente {user_id}")

    return db_item
