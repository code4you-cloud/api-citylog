import re
import os
import requests
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.schemas.emaildata import EmailData, EmailDataCreate, EmailDataUpdate
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

FLASK_DELETE_ENDPOINT = "http://ws.citylog.cloud/upload/delete"  # Cambia con URL corretto server Flask
#FLASK_DELETE_ENDPOINT = "http://192.168.1.43:9000/upload/delete"  # Cambia con URL corretto server Flask

router = APIRouter(prefix="/rifiuti", tags=["Rifiuti"])

# Inizializza il logger
logger = setup_logging()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=EmailData, status_code=status.HTTP_201_CREATED)
async def create_rifiuti(
    item: EmailDataCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(
            UserModel.email == current_user["username"]
            ).first()

    if not db_user:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Utente non trovato")

    db_item = EmailDataModel(
            **item.dict(exclude={"typo", "user_id", "id", "image_time"}), 
            typo="rifiuti", 
            user_id=db_user.id)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(f"Creato record rifiuti con ID {db_item.id} da utente {current_user['username']}")
    return db_item

# Versione SENZA autenticazione - PER TESTING
@router.get("/no-auth", response_model=List[EmailData])
async def list_rifiuti_no_auth(city: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Endpoint di test senza autenticazione
    """
    try:
        # Recupera tutti i record rifiuti (senza filtro utente)
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "rifiuti")

        if city:
            records = records.filter(EmailDataModel.city.ilike(f"%{city}%"))
        records = records.all()
        
        # Filtra i record con latitude/longitude nulli o non validi
        valid_records = [
            record for record in records
            if record.latitude is not None and record.longitude is not None
            and isinstance(record.latitude, str) and isinstance(record.longitude, str)
            and record.latitude.strip() and record.longitude.strip()  # Assicura che non siano stringhe vuote
        ]

        logger.info(f"Recuperati {len(records)} record rifiuti (senza autenticazione), "
                    f"{len(valid_records)} validi dopo il filtraggio")
        
        if not valid_records:
            logger.warning("Nessun record valido trovato dopo il filtraggio")
            return []

        return valid_records

    except Exception as e:
        logger.error(f"Errore nel recupero rifiuti senza auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

# Versione SENZA autenticazione - PER TESTING
@router.get("/no-auth_", response_model=List[EmailData])
async def list_rifiuti_no_auth(db: Session = Depends(get_db)):
    """
    Endpoint di test senza autenticazione
    """
    try:
        # Recupera tutti i record rifiuti (senza filtro utente)
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "rifiuti").all()

        logger.info(f"Recuperati {len(records)} record rifiuti (senza autenticazione)")
        return records

    except Exception as e:
        logger.error(f"Errore nel recupero rifiuti senza auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

# Endpoint rifiuti SEMPLIFICATO (senza rate limiting interno)
@router.get("/no-auth__", response_model=List[EmailData])
async def list_rifiuti(db: Session = Depends(get_db)):
    # Il rate limiting è gestito dal middleware
    records = db.query(EmailDataModel).filter(
        EmailDataModel.typo == "rifiuti",
        EmailDataModel.user_id.is_(None)
    ).all()

    return records

#@router.get("/complete", response_model=List[EmailData])
#async def listrifiuti_public(db: Session = Depends(get_db)):
#    """Endpoint pubblico per recuperare dati rifiuti"""
#    records = db.query(EmailDataModel).filter(
#        EmailDataModel.typo == "rifiuti"
#        #EmailDataModel.is_public == True  # Aggiungi campo per dati pubblici
#    ).all()
#    return records
#

@router.get("/", response_model=List[EmailData])
async def list_rifiuti(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    user_records = db.query(EmailDataModel).filter(
        EmailDataModel.user_id == db_user.id,
        EmailDataModel.typo == "rifiuti"
    ).all()

    if not user_records and db.query(EmailDataModel).filter(
        EmailDataModel.user_id.is_(None),
        EmailDataModel.typo == "rifiuti"
    ).first():
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "rifiuti").all()
        logger.info(f"Recuperati {len(records)} record rifiuti con user_id vuoto per utente {current_user['username']}")
        return records

    logger.info(f"Recuperati {len(user_records)} record rifiuti per utente {current_user['username']}")
    return user_records

@router.put("/{id}", response_model=EmailData)
async def update_rifiuti(
    id: int,
    item: EmailDataUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "rifiuti").first()
    if not db_item:
        logger.warning(f"Tentativo di aggiornamento record rifiuti ID {id} non trovato da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a modificare record rifiuti ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    # Aggiorna i campi forniti
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)

    # Aggiorna image_time automaticamente
    db_item.image_time = datetime.utcnow()

    db.commit()
    db.refresh(db_item)
    logger.info(f"Aggiornato record rifiuti ID {id} da utente {current_user['username']}")
    return db_item


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_rifiuti(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1.Recupera utente
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        logger.warning(f"Utente {current_user['username']} non trovato per eliminazione record rifiuti ID {id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    # 2.Recupera record rifiuti
    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "rifiuti").first()
    if not db_item:
        logger.warning(f"Record rifiuti ID {id} non trovato per eliminazione da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    # 3.Controlla autorizzazione
    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a eliminare record rifiuti ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    # 4.Cancella fisicamente il file tramite endpoint Flask
    delete_file_success = False
    if db_item.image_url:
        filename = os.path.basename(db_item.image_url)
        remote_path = f"uploaded_images/{filename}"
        try:
            flask_resp = requests.delete(f"{FLASK_DELETE_ENDPOINT}/{remote_path}", timeout=10)
            #flask_resp = requests.delete(f"{FLASK_DELETE_ENDPOINT}/{filename}", timeout=10)
            logger.info(f"ENDPOINT FINALE DI DELETE:{FLASK_DELETE_ENDPOINT}/{remote_path}")
            if flask_resp.status_code == 200:
                delete_file_success = True
                logger.info(f"File remoto '{filename}' eliminato correttamente tramite Flask")
            else:
                logger.warning(f"Fallita cancellazione file remoto '{filename}' tramite Flask. Status: {flask_resp.status_code}")
        except requests.RequestException as e:
            logger.error(f"Errore nella richiesta DELETE verso Flask per file '{filename}': {e}")

    # 5. Cancella record dal DB
    db.delete(db_item)
    db.commit()
    logger.info(f"Record rifiuti ID {id} eliminato da utente {current_user['username']}")

    # 6. Restituisce messaggio chiaro
    return {
        "detail": f"Record ID {id} cancellato dal database" +
                  (", file fisico eliminato con successo" if delete_file_success else ", ma file fisico non eliminato")
    }

@router.get("/legacy/resolve-image-id")
async def resolve_image_id_from_filename(
    filename: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("========== DEBUG resolve-image-id ==========")
    print("FILENAME ricevuto:", filename)

    records = db.query(EmailDataModel.image_url).filter(
        EmailDataModel.typo == "rifiuti"
    ).all()

    print(f"Trovati {len(records)} record rifiuti nel DB")
    for r in records:
        print("DB URL:", r.image_url)

    # ---- QUERY REALE (per ora lasciamola così) ----
    record = db.query(EmailDataModel).filter(
        EmailDataModel.typo == "rifiuti",
        EmailDataModel.image_url.ilike(f"%{filename}%")
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato")

    return {
        "id": record.id,
        "image_id": record.image_id,
        "image_url": record.image_url
    }
