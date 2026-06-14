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

@router.get("/me/rate-limit", response_model=list[UserRateLimitResponse]
)
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
        return RateLimitResponse(
            user_id=current_user.id,
            report_count=0,
            limit=5,
            remaining=5,
            is_banned=False,
            updated_at=datetime.utcnow()
        )

    return RateLimitResponse(
        user_id=current_user.id,
        report_count=rl.count,
        limit=5,
        remaining=max(0, 5 - rl.count),

        is_banned=rl.is_banned,
        ban_reason=rl.ban_reason,
        banned_until=rl.banned_until,

        updated_at=rl.updated_at
    )
