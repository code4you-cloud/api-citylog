from fastapi import FastAPI
from app.routers import auth, users, rifiuti, tronchi, censimento, piantumazioni, strade, segnalazioni, quartieri
from app.middlewares.rate_limiter import RateLimiterMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.logging_config import setup_logging

from app.models.user_rate_limit import UserRateLimit

# Inizializza il logging
logger = setup_logging()

# Crea le tabelle del database
Base.metadata.create_all(bind=engine)

# Crea l'app FastAPI
app = FastAPI(
    title="FastAPI Project Citylog with JWT Auth",
    description="API with authentication, rate limiting, endpoints for Rifiuti, Ambiente, Strade, Piantumazioni -58",
    version="1.0.0"
    #redirect_slashes=False
)

# Origini consentite (CORS)
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.1.58:4000",
    "https://citylog.cloud",
    "https://www.citylog.cloud",
    "https://maps.citylog.cloud",
    "*",
]

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware Rate Limiter
# Limite di 1000 richieste per 24 ore (86400 secondi)
app.add_middleware(RateLimiterMiddleware, limit=1000, window=86400)

# Includi i router
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(segnalazioni.router)
app.include_router(rifiuti.router)
app.include_router(tronchi.router)
app.include_router(censimento.router)
app.include_router(piantumazioni.router)
app.include_router(strade.router)
app.include_router(quartieri.router)

@app.get("/", tags=["Root", "Health"])
def root():
    return {
        "message": "Welcome to CityLog API",
        "docs": "/docs",
        "status": "online",
        "version": app.version  # opzionale, usa la versione dell'app
    }

# Log di avvio
logger.info("Applicazione FastAPI avviata")
