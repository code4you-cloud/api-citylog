import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.models.redaction_box_model import RedactionBoxModel
from app.schemas.emaildata import EmailData, EmailDataCreate, EmailDataUpdate
from app.auth.dependencies import get_current_user
from app.logging_config import setup_logging
from datetime import datetime

from app.middlewares.rate_limiter import RateLimiterMiddleware

from app.logging_config import setup_logging
from datetime import datetime
from typing import List, Optional


from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# RATE_LIMIT worrkflow
from services_rate_limit import check_and_increment_rate_limit
from config import MAX_REPORT_LIMIT, REMOTE_UPLOAD_URL, REMOTE_MEDIA_URL, AUTO_REDACT_THRESHOLD, REDACTED_OUTPUT_DIR

# ANTHROPIC and face and plating workflow detect
from config import ENABLE_ANTROPIC
from app.services.detection import detect_sensitive_regions, resolve_image_path
from app.services.redaction import apply_redaction_simple, upload_redacted_to_remote, build_redacted_filename, redact_and_swap

router = APIRouter(prefix="/strade", tags=["Strade"])

# Inizializza il logger
logger = setup_logging()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=EmailData, status_code=status.HTTP_201_CREATED)
async def create_strade(
    item: EmailDataCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = item.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    check_and_increment_rate_limit(db, user_id)

    db_item = EmailDataModel(
        **item.dict(exclude={"typo", "user_id", "id", "image_time", "status"}),
        typo="strade",
        user_id=user_id,
        status="api-city-log-cloud_create-rifiuto"
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(f"Creato record strade con ID {db_item.id} da utente {current_user['username']}")

    # --- HOOK: analisi immagine + redazione automatica + scrittura status_int ---
    if ENABLE_ANTROPIC:
        try:
            image_path = resolve_image_path(db_item)
            regions = detect_sensitive_regions(image_path)
        except Exception:
            logger.exception(f"Detection fallita per record {db_item.id}")
            db_item.status_int = 50  # ERROR
        else:
            if regions:
                all_high_conf = all(r.get('confidence', 0) >= AUTO_REDACT_THRESHOLD for r in regions)

                new_boxes = []
                for r in regions:
                    box = RedactionBoxModel(
                        report_id=db_item.id,
                        box_type=r['type'],
                        x=r['x'], y=r['y'], w=r['w'], h=r['h'],
                        confidence=r.get('confidence', 1.0),
                        confirmed=all_high_conf,
                        is_manual=False,
                    )
                    db.add(box)
                    new_boxes.append(box)

                if all_high_conf:
                    db.flush()  # popola gli id dei box prima della redazione
                    try:
                        local_redacted_path = apply_redaction_simple(
                            image_path, new_boxes, output_dir=REDACTED_OUTPUT_DIR, report_id=db_item.id
                        )
                        original_filename = db_item.image_url.split('/')[-1]

                        original_backup_url = redact_and_swap(
                            image_path, local_redacted_path, original_filename,
                            upload_base_url=REMOTE_UPLOAD_URL, media_base_url=REMOTE_MEDIA_URL
                        )

                        db_item.redacted_image = original_backup_url  # ora traccia l'ORIGINALE preservato, non la redatta
                        db_item.status_int = 20  # PUBLISHED, redatto automaticamente
                    except Exception:
                        logger.exception(f"Redazione automatica fallita per record {db_item.id}")
                        db_item.status_int = 40  # fallback: richiede revisione umana
                else:
                    db_item.status_int = 40  # FLAGGED, confidence non abbastanza alta
            else:
                db_item.status_int = 20  # PUBLISHED, nessun elemento sensibile

        db.commit()
        db.refresh(db_item)
    # -- END HOOK

    return db_item

@router.get("/no-auth", response_model=List[EmailData])
async def list_strade_no_auth(city: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Endpoint di test senza autenticazione per strade
    """
    try:
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "strade")
        if city:
            records = records.filter(EmailDataModel.city.ilike(f"%{city}%"))
        records = records.all()

        valid_records = [
            record for record in records
            if record.latitude is not None and record.longitude is not None
            and isinstance(record.latitude, str) and isinstance(record.longitude, str)
            and record.latitude.strip() and record.longitude.strip()
        ]

        logger.info(f"Recuperati {len(records)} record strade (senza autenticazione), "
                    f"{len(valid_records)} validi dopo il filtraggio")
        if not valid_records:
            logger.warning("Nessun record valido trovato dopo il filtraggio")
            return []

        return valid_records
    except Exception as e:
        logger.error(f"Errore nel recupero strade senza auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )

@router.get("/", response_model=List[EmailData])
async def list_strade(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    user_records = db.query(EmailDataModel).filter(
        EmailDataModel.user_id == db_user.id,
        EmailDataModel.typo == "strade"
    ).all()

    if not user_records and db.query(EmailDataModel).filter(
        EmailDataModel.user_id.is_(None),
        EmailDataModel.typo == "strade"
    ).first():
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "strade").all()
        logger.info(f"Recuperati {len(records)} record strade con user_id vuoto per utente {current_user['username']}")
        return records

    logger.info(f"Recuperati {len(user_records)} record strade per utente {current_user['username']}")
    return user_records

@router.put("/{id}", response_model=EmailData)
async def update_strade(
    id: int,
    item: EmailDataUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "strade").first()
    if not db_item:
        logger.warning(f"Tentativo di aggiornamento record strade ID {id} non trovato da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a modificare record strade ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    # Aggiorna i campi forniti
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)

    # Aggiorna image_time automaticamente
    db_item.image_time = datetime.utcnow()

    db.commit()
    db.refresh(db_item)
    logger.info(f"Aggiornato record strade ID {id} da utente {current_user['username']}")
    return db_item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strade(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        logger.warning(f"Utente {current_user['username']} non trovato per eliminazione record strade ID {id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "strade").first()
    if not db_item:
        logger.warning(f"Record strade ID {id} non trovato per eliminazione da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a eliminare record strade ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    db.delete(db_item)
    db.commit()
    logger.info(f"Eliminato record strade ID {id} da utente {current_user['username']}")
