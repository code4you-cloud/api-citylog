import logging
import requests

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status,Body
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.db.database import SessionLocal
from app.models.user import User as UserModel
from app.auth.jwt_handler import verify_password
from sqlalchemy.orm import Session


from app.auth.jwt_handler import verify_password, get_password_hash
from app.schemas.emaildata import FacebookAuthRequest

logger = logging.getLogger(__name__)

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

@router.post("/auth/facebook")
async def facebook_auth(
    request: FacebookAuthRequest,
    db: Session = Depends(get_db)
):
    facebook_token = request.access_token
    if not facebook_token:
        logger.warning("Richiesta senza access_token")
        raise HTTPException(status_code=400, detail="Manca il campo 'access_token'")

    logger.info(f"Login Facebook con token: {facebook_token[:20]}...")

    # Step 1: Verifica token con Facebook Graph API
    try:
        fb_response = requests.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email",
                "access_token": facebook_token
            },
            timeout=10,
            headers={"Accept": "application/json"}
        )

        logger.info(f"Facebook status: {fb_response.status_code}")
        logger.debug(f"Facebook response: {fb_response.text}")

        if fb_response.status_code != 200:
            try:
                error_data = fb_response.json()
                error_msg = error_data.get("error", {}).get("message", "Errore sconosciuto")
            except ValueError:
                error_msg = fb_response.text or "Risposta non JSON da Facebook"

            logger.error(f"Facebook errore: {error_msg}")
            raise HTTPException(
                status_code=401,
                detail=f"Token Facebook non valido: {error_msg}"
            )

        fb_data = fb_response.json()

    except requests.exceptions.RequestException as re:
        logger.error(f"Errore rete verso Facebook: {re}", exc_info=True)
        raise HTTPException(status_code=502, detail="Impossibile contattare Facebook")

    # Step 2: Estrai dati obbligatori
    fb_id = fb_data.get("id")
    if not fb_id:
        logger.warning("Facebook non ha restituito ID utente")
        raise HTTPException(status_code=400, detail="Impossibile ottenere ID Facebook")

    name = fb_data.get("name") or "Utente Facebook"

    # Step 3: Cerca o crea utente
    try:
        user = db.query(UserModel).filter(UserModel.facebook_id == fb_id).first()

        if not user:
            logger.info(f"Creazione nuovo utente con facebook_id: {fb_id}")
            logger.error(UserModel.__table__.columns.keys())
            user = UserModel(
                facebook_id=fb_id,
                email=fb_data.get("email"),
                name=name,
                username=f"fb_{fb_id}",     #OBBLIGATORIO
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Utente creato con ID interno: {user.id}")

        else:
            logger.info(f"Utente esistente trovato: {user.id}")
            # Aggiornamento opzionale
            if user.name != name:
                user.name = name
                db.commit()
                db.refresh(user)

    except Exception as db_error:
        logger.error(f"Errore database: {db_error}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Errore durante gestione utente")

    # Step 4: Genera JWT
    try:
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "fb_id": fb_id,
                "name": user.name,
                "username": user.username,
                "email": user.email,
            },
            expires_delta=timedelta(days=7)
        )
    except Exception as jwt_error:
        logger.error(f"Errore generazione JWT: {jwt_error}", exc_info=True)
        raise HTTPException(status_code=500, detail="Errore interno durante generazione token")

    # Step 5: Response strutturata
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email
        }
    }
