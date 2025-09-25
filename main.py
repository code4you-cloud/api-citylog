from fastapi import FastAPI
from app.routers import auth, users, rifiuti, tronchi, censimento, piantumazioni, strade
from app.middlewares.rate_limiter import RateLimiterMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.logging_config import setup_logging

# Inizializza il logging
logger = setup_logging()

# Crea le tabelle del database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Project with JWT Auth",
    description="API with authentication, rate limiting, and endpoints for Rifiuti, Ambiente, Strade, Brent",
    version="1.0.0"
)

# Origini consentite (puoi mettere '*' per tutte)
origins = [
    "http://localhost",              # sviluppo locale
    "http://127.0.0.1",
    "http://192.168.1.159",           # IP locale
    "https://citylog.cloud",          # dominio Django
    "https://www.citylog.cloud",          # dominio Django
    "https://maps.citylog.cloud",          # dominio Django
    "*",
]

# Aggiungi il middleware con limite giornaliero
app.add_middleware(
    RateLimiterMiddleware,
    #limit=1000,      #richieste
    #window=86400,    # per 24 ore (86400 secondi)
    CORSMiddleware,
    allow_origins=origins, # chi può chiamare le API
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, PUT, DELETE, ecc.
    allow_headers=["*"], # tutti gli header
)

app.add_middleware(RateLimiterMiddleware, limit=1000, window=86400)  # limite giornaliero
app.add_middleware(RateLimiterMiddleware, limit=100, window=60)      # limite minuto

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rifiuti.router)
app.include_router(tronchi.router)
app.include_router(censimento.router)
app.include_router(piantumazioni.router)
app.include_router(strade.router)

# Log di avvio
logger.info("Applicazione FastAPI avviata")
