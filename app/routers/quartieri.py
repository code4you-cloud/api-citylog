import re
import os
import requests
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.schemas.quartieri import QuartiereUpdateItem, QuartiereBatchUpdate
from app.auth.dependencies import get_current_user

from app.middlewares.rate_limiter import RateLimiterMiddleware

from app.logging_config import setup_logging
from datetime import datetime
from typing import List, Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from datetime import timedelta
from sqlalchemy import func, and_
from urllib.parse import urlparse

# -----------------------------
# COSTANTI GLOBALI
# -----------------------------

FLASK_DELETE_ENDPOINT = "https://ws.citylog.cloud/upload/delete"  # Cambia con URL corretto server Flask
#FLASK_DELETE_ENDPOINT = "http://192.168.1.43:9000/upload/delete"  # Cambia con URL corretto server Flask

router = APIRouter(prefix="/quartieri", tags=["Quartieri"])

# Inizializza il logger
logger = setup_logging()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/batch-update")
async def batch_update_quartieri(
    payload: QuartiereBatchUpdate,
    db: Session = Depends(get_db)
):
    updated = 0
    not_found = 0

    for item in payload.updates:
        record = None

        # 0. Cerca per image_id (il più affidabile)
        if item.image_id is not None:
            record = db.query(EmailDataModel).filter(
                EmailDataModel.image_id == item.image_id
            ).first()
            print(f"DEBUG: cercato per image_id={item.image_id}, trovato={record is not None}")

        # 1. Altrimenti cerca per ID numerico
        if record is None and item.id is not None:
            record = db.query(EmailDataModel).filter(
                EmailDataModel.id == item.id
            ).first()
            print(f"DEBUG: cercato per id={item.id}, trovato={record is not None}")

        # 2. Altrimenti cerca per coordinate e typo
        if record is None and item.latitudine is not None and item.longitudine is not None:
            try:
                lat_str = f"{float(item.latitudine):.6f}"
                lon_str = f"{float(item.longitudine):.6f}"
            except ValueError:
                print(f"DEBUG: coordinate non valide: lat={item.latitudine}, lon={item.longitudine}")
                not_found += 1
                continue

            record = db.query(EmailDataModel).filter(
                and_(
                    EmailDataModel.latitude == lat_str,
                    EmailDataModel.longitude == lon_str,
                    EmailDataModel.typo == item.typo
                )
            ).first()
            print(f"DEBUG: cercato per lat={lat_str}, lon={lon_str}, typo={item.typo}, trovato={record is not None}")

        if record:
            record.quartiere = item.quartiere
            db.flush()
            print(f"DEBUG: aggiornato record ID={record.id} con quartiere={item.quartiere}")
            updated += 1
        else:
            print(f"DEBUG: record non trovato per item: {item.dict()}")
            not_found += 1

    db.commit()
    print(f"DEBUG: commit eseguito. updated={updated}, not_found={not_found}")
    return {"status": "ok", "updated": updated, "not_found": not_found}

@router.post("/batch-update_last")
async def batch_update_quartieri_last(
    payload: QuartiereBatchUpdate,
    db: Session = Depends(get_db)
):
    updated = 0
    not_found = 0

    for item in payload.updates:
        record = None

        # 1. Preferisci sempre l'ID (se fornito)
        if item.id is not None:
            record = db.query(EmailDataModel).filter(EmailDataModel.id == item.id).first()

        # 2. Altrimenti cerca per coordinate (stringhe) e typo
        elif item.latitudine is not None and item.longitudine is not None:
            # Normalizza: arrotonda a 6 decimali e converti in stringa
            try:
                lat_str = f"{float(item.latitudine):.6f}"
                lon_str = f"{float(item.longitudine):.6f}"
            except ValueError:
                not_found += 1
                continue

            record = db.query(EmailDataModel).filter(
                and_(
                    EmailDataModel.latitude == lat_str,
                    EmailDataModel.longitude == lon_str,
                    EmailDataModel.typo == item.typo
                )
            ).first()

        if record:
            record.quartiere = item.quartiere
            db.flush()  # forza la scrittura senza commit finale
            updated += 1
        else:
            not_found += 1

    db.commit()
    return {"status": "ok", "updated": updated, "not_found": not_found}

# con la/long real
@router.post("/batch-update_")
async def batch_update_quartieri_(
    payload: QuartiereBatchUpdate, 
    db: Session = Depends(get_db)
):
    updated = 0
    not_found = 0

    for item in payload.updates:
        record = None

        # 1. Ricerca per ID (se fornito)
        if item.id is not None:
            record = db.query(EmailDataModel).filter(EmailDataModel.id == item.id).first()

        # 2. Altrimenti ricerca per coordinate e tipo
        elif item.lat is not None and item.lon is not None:
            lat = round(item.lat, 6)
            lon = round(item.lon, 6)
            record = db.query(EmailDataModel).filter(
                and_(
                    EmailDataModel.latitude == lat,
                    EmailDataModel.longitude == lon,
                    EmailDataModel.tipo == item.type
                )
            ).first()

        if record:
            record.quartiere = item.quartiere   # UPDATE QUARTIERE
            updated += 1
        else:
            not_found += 1

    db.commit()  # Salva tutte le modifiche

    return {"status": "ok", "updated": updated, "not_found": not_found}
