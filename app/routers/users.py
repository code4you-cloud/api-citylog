import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User
from app.auth.dependencies import get_current_user
from app.auth.jwt_handler import get_password_hash

#from app.database import get_db
from app.models.citylog import EmailData as EmailDataModel
from app.schemas.emaildata import SegnalazioneOut
from app.schemas.user_rate_limit import UserRateLimitResponse

from app.models.user_rate_limit import UserRateLimit
from datetime import datetime

from config import MAX_REPORT_LIMIT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        email=user.email,
        hashed_password=hashed_password,
        username=user.username
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=User)
async def read_current_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.email == current_user["username"]).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.get("/me/segnalazioni", response_model=list[SegnalazioneOut])
def get_my_segnalazioni(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Current user in segnalazioni: {current_user}")
    logger.info(f"Type of current_user: {type(current_user)}")
    
    # Tentativo con diverse chiavi
    user_id = current_user.get('id') or current_user.get('sub') or current_user.get('user_id')
    if user_id is None:
        # Se è un oggetto, prova attributo
        if hasattr(current_user, 'id'):
            user_id = current_user.id
        else:
            # Log completo del dizionario per debug
            raise HTTPException(status_code=401, detail=f"Token non valido: impossibile trovare id in {current_user}")
    
    segnalazioni = (
        db.query(EmailDataModel)
        .filter(EmailDataModel.user_id == user_id)
        .order_by(EmailDataModel.image_time.desc())
        .all()
    )
    return segnalazioni

@router.get("/me/segnalazioni_", response_model=list[SegnalazioneOut])
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

@router.get("/me/rate-limit", response_model=UserRateLimitResponse)  # attenzione: non list
def get_my_rate_limit(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get('id') or current_user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    # Recupera il record del rate limit (limite massimo personalizzato, se esiste)
    rl = db.query(UserRateLimit).filter(UserRateLimit.user_id == user_id).first()

    if not rl:
        return UserRateLimitResponse(
            user_id=user_id,   # usa user_id, non current_user.id
            count=MAX_REPORT_LIMIT,
            sent=0,
            is_banned=False,
            updated_at=datetime.utcnow()
        )
    else:
        return UserRateLimitResponse(
            user_id=user_id,       # e anche qui
            count=rl.count,        # limite massimo
            sent=rl.sent,          # segnalazioni effettive
            is_banned=rl.is_banned,
            ban_reason=rl.ban_reason,
            banned_until=rl.banned_until,
            updated_at=rl.updated_at
        )

@router.get("/me/rate-limit_", response_model=UserRateLimitResponse)
def get_my_rate_limit(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get('id') or current_user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    rl = (
        db.query(UserRateLimit)
        .filter(
            UserRateLimit.user_id == user_id
        )
        .first()
    )

    if not rl:
        return UserRateLimitResponse(
            user_id=current_user.id,
            report_count=0,
            limit=5,
            remaining=5,
            is_banned=False,
            updated_at=datetime.utcnow()
        )

    return UserRateLimitResponse(
        user_id=current_user.id,
        report_count=rl.count,
        limit=5,
        remaining=max(0, 5 - rl.count),

        is_banned=rl.is_banned,
        ban_reason=rl.ban_reason,
        banned_until=rl.banned_until,

        updated_at=rl.updated_at
    )
