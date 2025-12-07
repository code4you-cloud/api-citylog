from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.jwt_handler import SECRET_KEY, ALGORITHM, JWTError, jwt, TokenData

from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User as UserModel


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali di autenticazione non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decodifica il token JWT
        payload = verify_token(token)  # Usa la funzione dal tuo jwt_handler

        # Estrai le informazioni dal payload
        user_id: Optional[str] = payload.get("sub")
        username: Optional[str] = payload.get("username")
        facebook_id: Optional[str] = payload.get("facebook_id")

        if not user_id:
            raise credentials_exception

        # Cerca l'utente nel database usando l'ID
        user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()

        # Se non trovato per ID, prova a cercare per Facebook ID
        if not user and facebook_id:
            user = db.query(UserModel).filter(UserModel.facebook_id == facebook_id).first()

        # Se ancora non trovato, cerca per email (per compatibilità con vecchio sistema)
        if not user and username:
            user = db.query(UserModel).filter(UserModel.email == username).first()

        if not user:
            raise credentials_exception

        # Verifica che l'utente sia attivo
        if hasattr(user, 'is_active') and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabilitato"
            )

        # Restituisce un dizionario con i dati dell'utente
        user_data = {
            "id": user.id,
            "username": user.email or user.facebook_id or str(user.id),
            "email": user.email,
            "facebook_id": user.facebook_id,
            "full_name": getattr(user, 'full_name', None)
        }

        return user_data

    except Exception as e:
        # Log dell'errore (dovresti avere un logger configurato)
        # logger.error(f"Errore durante l'autenticazione: {str(e)}")
        raise credentials_exception

async def get_current_user__(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except JWTError:
        raise credentials_exception
