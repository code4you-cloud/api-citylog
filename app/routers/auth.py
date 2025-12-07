from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.db.database import SessionLocal
from app.models.user import User as UserModel
from app.auth.jwt_handler import verify_password
from sqlalchemy.orm import Session


from app.auth.jwt_handler import verify_password, get_password_hash

router = APIRouter(tags=["Authentication"])

# Configurazione Facebook (da mettere in variabili d'ambiente)
FB_APP_ID = "your-facebook-app-id"
FB_APP_SECRET = "your-facebook-app-secret"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user

async def verify_facebook_token(access_token: str) -> Optional[dict]:
    """Verifica il token Facebook con Graph API"""
    async with httpx.AsyncClient() as client:
        try:
            # Verifica il token
            verify_url = "https://graph.facebook.com/debug_token"
            params = {
                "input_token": access_token,
                "access_token": f"{FB_APP_ID}|{FB_APP_SECRET}"
            }

            verify_resp = await client.get(verify_url, params=params)
            verify_data = verify_resp.json()

            if "error" in verify_data or not verify_data.get("data", {}).get("is_valid", False):
                return None

            # Ottieni i dati utente
            user_url = "https://graph.facebook.com/me"
            params = {
                "access_token": access_token,
                "fields": "id,name,email,picture"
            }

            user_resp = await client.get(user_url, params=params)
            user_data = user_resp.json()

            if "error" in user_data:
                return None

            return user_data

        except Exception:
            return None

@router.post("/auth/facebook")
async def facebook_login(
    access_token: str,
    db: Session = Depends(get_db)
):
    """Login con token Facebook"""
    # Verifica il token con Facebook
    user_data = await verify_facebook_token(access_token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Facebook non valido"
        )
    
    facebook_id = user_data["id"]
    email = user_data.get("email")
    full_name = user_data.get("name")
    
    # Cerca utente per Facebook ID
    user = db.query(UserModel).filter(
        UserModel.facebook_id == facebook_id
    ).first()
    
    # Se non trovato, cerca per email (per unire account)
    if not user and email:
        user = db.query(UserModel).filter(
            UserModel.email == email
        ).first()
        
        # Se trovato per email, aggiorna con Facebook ID
        if user:
            user.facebook_id = facebook_id
            db.commit()
    
    # Se ancora non trovato, crea nuovo utente
    if not user:
        user = UserModel(
            facebook_id=facebook_id,
            email=email,
            full_name=full_name,
            is_active=True,
            is_verified=True  # Facebook verifica l'email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Genera token JWT
    access_token_expires = timedelta(days=7)  # Più lungo per social login
    token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.email or user.facebook_id,
            "facebook_id": user.facebook_id
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "facebook_id": user.facebook_id,
        "email": user.email
    }


@router.post("/auth/register")
async def register_user(
    email: str,
    password: str,
    full_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Registrazione tradizionale"""
    # Verifica se l'utente esiste già
    existing_user = db.query(UserModel).filter(
        (UserModel.email == email) |
        (UserModel.facebook_id.isnot(None) & (UserModel.email == email))
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata"
        )

    # Crea nuovo utente
    user = UserModel(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Genera token
    access_token_expires = timedelta(minutes=30)
    token = create_access_token(
        data={"sub": str(user.id), "username": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id
