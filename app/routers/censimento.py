from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.citylog import EmailData as EmailDataModel
from app.models.user import User as UserModel
from app.schemas.emaildata import EmailData, EmailDataCreate, EmailDataUpdate
from app.auth.dependencies import get_current_user
from app.logging_config import setup_logging
from datetime import datetime
from typing import List

router = APIRouter(prefix="/censimento", tags=["Censimento"])

# Inizializza il logger
logger = setup_logging()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=EmailData, status_code=status.HTTP_201_CREATED)
async def create_censimento(
    item: EmailDataCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = EmailDataModel(**item.dict(), typo="censimento", user_id=db_user.id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    logger.info(f"Creato record censimento con ID {db_item.id} da utente {current_user['username']}")
    return db_item

@router.get("/", response_model=List[EmailData])
async def list_censimento(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    user_records = db.query(EmailDataModel).filter(
        EmailDataModel.user_id == db_user.id,
        EmailDataModel.typo == "censimento"
    ).all()

    if not user_records and db.query(EmailDataModel).filter(
        EmailDataModel.user_id.is_(None),
        EmailDataModel.typo == "censimento"
    ).first():
        records = db.query(EmailDataModel).filter(EmailDataModel.typo == "cendimento").all()
        logger.info(f"Recuperati {len(records)} record censimento con user_id vuoto per utente {current_user['username']}")
        return records

    logger.info(f"Recuperati {len(user_records)} record censimento per utente {current_user['username']}")
    return user_records

@router.put("/{id}", response_model=EmailData)
async def update_censimento(
    id: int,
    item: EmailDataUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "cendimento").first()
    if not db_item:
        logger.warning(f"Tentativo di aggiornamento record censimento ID {id} non trovato da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a modificare record censimento ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    # Aggiorna i campi forniti
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)

    # Aggiorna image_time automaticamente
    db_item.image_time = datetime.utcnow()

    db.commit()
    db.refresh(db_item)
    logger.info(f"Aggiornato record censimento ID {id} da utente {current_user['username']}")
    return db_item

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_censimento(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        logger.warning(f"Utente {current_user['username']} non trovato per eliminazione record censimento ID {id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    db_item = db.query(EmailDataModel).filter(EmailDataModel.id == id, EmailDataModel.typo == "censimento").first()
    if not db_item:
        logger.warning(f"Record censimento ID {id} non trovato per eliminazione da utente {current_user['username']}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record non trovato")

    if db_item.user_id is not None and db_item.user_id != db_user.id:
        logger.warning(f"Utente {current_user['username']} non autorizzato a eliminare record censimento ID {id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorizzato")

    db.delete(db_item)
    db.commit()
    logger.info(f"Eliminato record censimento ID {id} da utente {current_user['username']}")
