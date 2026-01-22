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
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = EmailDataModel(**item.dict(), typo="rifiuti", user_id=db_user.id)
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

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rifiuti(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        logger.warning(f"Utente {current_user['username']} non trovato per eliminazione record rifiuti ID {id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "rifiuti").first()
    if not db_item:
        logger.warning(f"Record rifiuti ID {id} non trovato per eliminazione da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a eliminare record rifiuti ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    db.delete(db_item)
    db.commit()
    logger.info(f"Eliminato record rifiuti ID {id} da utente {current_user['username']}")

@router.get("/record/", response_model=EmailData)
async def get_single_rifiuto(
    latitude: str,
    longitude: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    # Cerca il record specifico
    query = db.query(EmailDataModel).filter(
        EmailDataModel.typo == "rifiuti",
        EmailDataModel.latitude == latitude,
        EmailDataModel.longitude == longitude
    )
    
    # Applica le regole di accesso
    user_has_records = db.query(EmailDataModel).filter(
        EmailDataModel.user_id == db_user.id,
        EmailDataModel.typo == "rifiuti"
    ).first() is not None
    
    if user_has_records:
        query = query.filter(EmailDataModel.user_id == db_user.id)
    else:
        query = query.filter(EmailDataModel.user_id.is_(None))
    
    record = query.first()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Record non trovato o accesso non autorizzato"
        )
    
    return record
