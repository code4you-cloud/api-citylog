import logging
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.jwt_handler import SECRET_KEY, ALGORITHM, JWTError, jwt, TokenData
from app.db.database import SessionLocal
from app.models.user import User as UserModel

# Definisci il logger per questo modulo specifico
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        
        if user_id is None:
            user_id = payload.get("sub")
            
        if user_id is None:
            raise credentials_exception
            
        # Converte in int se necessario
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise credentials_exception
        
        # VERIFICA CHE L'UTENTE ESISTA NEL DATABASE
        print(f"Cerco user_id: {user_id}")  # DEBUG
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        print(f"Utente trovato: {user.id}")    # DEBUG

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Restituisci l'oggetto User completo o un dict con i dati
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            # altri campi se necessari
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERRORE: {e}")  # DEBUG - VEDI QUESTO
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating user"
        )

async def get_current_user_(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            # Per compatibilità con token che usano 'sub'
            user_id = payload.get("sub")
            if user_id is not None:
                user_id = int(user_id)
        if user_id is None:
            raise credentials_exception

        return {
            "id": user_id,
            "username": payload.get("username"),
            "email": payload.get("email"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"SECRET VERIFY -> {SECRET_KEY}")
        logger.info(f"VERIFY ALG -> {ALGORITHM}")
        logger.info(f"JWT OK -> {payload}")
        logger.info(f"TOKEN ARRIVATO {token}")
        logger.info(f"PAYLOAD {payload}")

        #change for google
        payload["id"] = int(payload.get("sub", 0))
        return payload
        #username: str = payload.get("sub")
        #if username is None:
        #    raise credentials_exception
        #return {"username": username}
    except JWTError as e:
        logger.error(f"JWT ERROR -> {e}")
        logger.warning(f"SECRET VERIFY -> {SECRET_KEY}")
        logger.warning(f"VERIFY ALG -> {ALGORITHM}")
        logger.warning(f"TOKEN JWTError -> {token}")
        #logger.warning(f"PAYLOAD -> {payload}")
        raise HTTPException(status_code=401, detail="Invalid token")
        #raise credentials_exception
