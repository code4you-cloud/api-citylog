from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.auth.jwt_handler import SECRET_KEY, ALGORITHM, JWTError, jwt, TokenData
import logging

# Definisci il logger per questo modulo specifico
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
