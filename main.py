from fastapi import FastAPI
from app.routers import auth, users, rifiuti, tronchi, censimento, piantumazioni, strade
from app.middlewares.rate_limiter import RateLimiterMiddleware
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

# Aggiungi il middleware con limite giornaliero
app.add_middleware(
    RateLimiterMiddleware,
    limit=2      # 1000 richieste
    #window=86400     # per 24 ore (86400 secondi)
)

app.add_middleware(RateLimiterMiddleware, limit=100, window=60)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(rifiuti.router)
app.include_router(tronchi.router)
app.include_router(censimento.router)
app.include_router(piantumazioni.router)
app.include_router(strade.router)

# Log di avvio
logger.info("Applicazione FastAPI avviata")
