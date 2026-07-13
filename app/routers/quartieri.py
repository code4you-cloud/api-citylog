import re
import os
import requests
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.schemas.quartieri import QuartiereUpdateItem, QuartiereBatchUpdate, QuartiereResponse
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

@router.get("/", response_model=List[QuartiereResponse])
async def get_quartieri(
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)   # usa il tuo metodo di autenticazione
):
    """
    Restituisce la lista dei quartieri con:
    - numero totale di segnalazioni
    - data dell'ultima segnalazione
    - coordinate (prese dal primo record per quel quartiere)
    """
    try:
        base_query = db.query(
            EmailDataModel.quartiere,
            func.count(EmailDataModel.id).label("totale"),
            func.max(EmailDataModel.image_time).label("ultima_data"),
            func.min(EmailDataModel.id).label("min_id")
        ).filter(
            EmailDataModel.quartiere.isnot(None),
            EmailDataModel.quartiere != ""
        )

        # Se vuoi mostrare solo i quartieri delle segnalazioni dell'utente loggato:
        # base_query = base_query.filter(EmailDataModel.user_id == current_user.id)

        if city:
            base_query = base_query.filter(EmailDataModel.city.ilike(f"%{city}%"))

        aggregated = base_query.group_by(EmailDataModel.quartiere).all()

        result = []
        for row in aggregated:
            quartiere_name = row.quartiere
            totale = row.totale
            ultima_data = row.ultima_data
            min_id = row.min_id

            # Recupera le coordinate dal record con ID minimo
            record = db.query(EmailDataModel).filter(EmailDataModel.id == min_id).first()
            lat = record.latitude if record else ""
            lon = record.longitude if record else ""

            data_str = ""
            if ultima_data:
                try:
                    data_str = ultima_data.strftime("%Y-%m-%d")
                except:
                    data_str = str(ultima_data)[:10]

            result.append(QuartiereResponse(
                quartiere=quartiere_name,
                segnalazioni_totali=totale,
                ultima_segnalazione=data_str,
                latitudine=lat,
                longitudine=lon
            ))

        logger.info(f"Quartieri trovati: {len(result)}")
        return result

    except Exception as e:
        logger.error(f"Errore nel recupero quartieri: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore interno del server")

@router.get("/no-auth", response_model=List[QuartiereResponse])
async def get_quartieri_no_auth(
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Restituisce i quartieri con statistiche e coordinate (primo record con lat/lon validi).
    """
    try:
        # 1. Raggruppa per quartiere e calcola totali + ultima data
        base_query = db.query(
            EmailDataModel.quartiere,
            func.count(EmailDataModel.id).label("totale"),
            func.max(EmailDataModel.image_time).label("ultima_data")
        ).filter(
            EmailDataModel.quartiere.isnot(None),
            EmailDataModel.quartiere != ""
        )

        if city:
            base_query = base_query.filter(EmailDataModel.city.ilike(f"%{city}%"))

        aggregated = base_query.group_by(EmailDataModel.quartiere).all()

        result = []
        for row in aggregated:
            quartiere_name = row.quartiere
            totale = row.totale
            ultima_data = row.ultima_data

            # 2. Per ogni quartiere, cerca il primo record con coordinate valide
            coord_record = db.query(EmailDataModel).filter(
                EmailDataModel.quartiere == quartiere_name,
                EmailDataModel.latitude.isnot(None),
                EmailDataModel.latitude != "",
                EmailDataModel.longitude.isnot(None),
                EmailDataModel.longitude != ""
            ).order_by(EmailDataModel.id.asc()).first()

            lat = coord_record.latitude if coord_record else ""
            lon = coord_record.longitude if coord_record else ""

            # Formatta la data (YYYY-MM-DD)
            data_str = ""
            if ultima_data:
                try:
                    data_str = ultima_data.strftime("%Y-%m-%d")
                except:
                    data_str = str(ultima_data)[:10]

            result.append(QuartiereResponse(
                quartiere=quartiere_name,
                segnalazioni_totali=totale,
                ultima_segnalazione=data_str,
                latitudine=lat,
                longitudine=lon
            ))

        logger.info(f"Quartieri trovati (no-auth): {len(result)}")
        return result

    except Exception as e:
        logger.error(f"Errore recupero quartieri: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore interno del server")

@router.get("/no-auth_", response_model=List[QuartiereResponse])
async def get_quartieri_(
    city: Optional[str] = None,
    db: Session = Depends(get_db)
    #current_user: User = Depends(get_current_user)   # usa il tuo metodo di autenticazione
):
    """
    Restituisce la lista dei quartieri con:
     - Versione di test senza autenticazione
    """
    try:
        base_query = db.query(
            EmailDataModel.quartiere,
            func.count(EmailDataModel.id).label("totale"),
            func.max(EmailDataModel.image_time).label("ultima_data"),
            func.min(EmailDataModel.id).label("min_id")
        ).filter(
            EmailDataModel.quartiere.isnot(None),
            EmailDataModel.quartiere != ""
        )

        # Se vuoi mostrare solo i quartieri delle segnalazioni dell'utente loggato:
        # base_query = base_query.filter(EmailDataModel.user_id == current_user.id)

        if city:
            base_query = base_query.filter(EmailDataModel.city.ilike(f"%{city}%"))

        aggregated = base_query.group_by(EmailDataModel.quartiere).all()

        result = []
        for row in aggregated:
            quartiere_name = row.quartiere
            totale = row.totale
            ultima_data = row.ultima_data
            min_id = row.min_id

            # Recupera le coordinate dal record con ID minimo
            record = db.query(EmailDataModel).filter(EmailDataModel.id == min_id).first()
            lat = record.latitude if record else ""
            lon = record.longitude if record else ""

            data_str = ""
            if ultima_data:
                try:
                    data_str = ultima_data.strftime("%Y-%m-%d")
                except:
                    data_str = str(ultima_data)[:10]

            result.append(QuartiereResponse(
                quartiere=quartiere_name,
                segnalazioni_totali=totale,
                ultima_segnalazione=data_str,
                latitudine=lat,
                longitudine=lon
            ))

        logger.info(f"Quartieri trovati: {len(result)}")
        return result

    except Exception as e:
        logger.error(f"Errore nel recupero quartieri: {str(e)}")
        raise HTTPException(status_code=500, detail="Errore interno del server")

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
