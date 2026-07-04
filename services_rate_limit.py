from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_rate_limit import UserRateLimit
from config import MAX_REPORT_LIMIT
from app.logging_config import setup_logging

# Inizializza il logger
logger = setup_logging()

def check_and_increment_rate_limit(
    db: Session,
    user_id: int
) -> UserRateLimit:

    now = datetime.utcnow()

    logger.warning(f"[RATE LIMIT] lookup user_id={user_id}")

    rl = (
        db.query(UserRateLimit)
        .filter(UserRateLimit.user_id == user_id)
        .first()
    )

    # Primo utilizzo: crea automaticamente il record
    if rl is None:
        logger.warning("[RATE LIMIT] Creo nuovo record")

        rl = UserRateLimit(
            user_id=user_id,
            count=MAX_REPORT_LIMIT,
            sent=0,
            is_banned=False
        )

        db.add(rl)
        db.commit()
        db.refresh(rl)

    logger.warning(
        f"[RATE LIMIT INCREMENT] "
        f"sent={rl.sent} "
        f"count={rl.count} "
        f"is_banned={rl.is_banned} "
        f"banned_until={rl.banned_until}"
    )

    # -----------------------------------------------------------------
    # BAN AMMINISTRATIVO
    # -----------------------------------------------------------------
    if (
        rl.is_banned
        and rl.banned_until
        and rl.banned_until > now
    ):
        logger.warning("[RATE LIMIT] BLOCCATO PER BAN")

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Utente bannato fino al {rl.banned_until}. Motivo: {rl.ban_reason}"
        )

    # Ban scaduto blocca automaticamente
    if (
        rl.is_banned
        and rl.banned_until
        and rl.banned_until <= now
    ):
        logger.warning("[RATE LIMIT] Ban scaduto")

        rl.is_banned = False
        rl.banned_until = None
        rl.ban_reason = None

    # -----------------------------------------------------------------
    # RATE LIMIT
    # -----------------------------------------------------------------
    if rl.sent >= rl.count:

        logger.warning("[RATE LIMIT] LIMITE RAGGIUNTO")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hai raggiunto il limite massimo di {rl.count} segnalazioni."
        )

    # -----------------------------------------------------------------
    # Incrementa il contatore
    # -----------------------------------------------------------------
    rl.sent += 1

    db.commit()
    db.refresh(rl)

    logger.warning(
        f"[RATE LIMIT] nuovo valore sent={rl.sent}/{rl.count}"
    )

    return rl

def check_and_increment_rate_limit__(db: Session, user_id: int) -> UserRateLimit:
    now = datetime.utcnow()

    logger.warning(f"[RATE LIMIT] lookup user_id={user_id}")

    rl = db.query(UserRateLimit).filter(UserRateLimit.user_id == user_id).first()
    logger.warning(f"[RATE LIMIT] record={rl}")

    # Se non esiste, crea il record con il limite massimo predefinito
    if not rl:
        logger.warning("[RATE LIMIT] Creo nuovo record")
        rl = UserRateLimit(user_id=user_id, count=MAX_REPORT_LIMIT, sent=0)
        db.add(rl)
        db.commit()

    # Controlla ban attivo
    if rl.is_banned and rl.banned_until and rl.banned_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Utente bannato fino al {rl.banned_until}. Motivo: {rl.ban_reason}"
        )

    # Controlla se ha raggiunto il limite massimo
    if rl.sent >= rl.count:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hai superato il limite di {rl.count} segnalazioni."
        )

    # INCREMENTA IL CONTATORE (SOLO DOPO I CONTROLLI)
    rl.sent += 1
    db.commit()

    # Se dopo l'incremento ha raggiunto il limite, banna automaticamente
    if rl.sent == rl.count:
        rl.is_banned = True
        rl.ban_reason = f"Limite di {rl.count} segnalazioni superato"
        rl.banned_until = now + timedelta(days=1)
        db.commit()

    return rl

def check_and_increment_rate_limit_ultima(db: Session, user_id: int) -> UserRateLimit:
    now = datetime.utcnow()

    rl = db.query(UserRateLimit).filter(UserRateLimit.user_id == user_id).first()

    # Se non esiste, crea il record con il limite massimo predefinito
    if not rl:
        rl = UserRateLimit(user_id=user_id, count=MAX_REPORT_LIMIT, sent=0)
        db.add(rl)
        db.commit()

    # Controlla ban attivo
    if rl.is_banned and rl.banned_until and rl.banned_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Utente bannato fino al {rl.banned_until}. Motivo: {rl.ban_reason}"
        )

    # Controlla se ha raggiunto il limite massimo
    if rl.sent >= rl.count:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hai superato il limite di {rl.count} segnalazioni."
        )

    # Incrementa il contatore delle inviate
    rl.sent += 1
    db.commit()

    # Se dopo lo incremento ha raggiunto il limite, banna automaticamente (opzionale)
    if rl.sent == rl.count:
        rl.is_banned = True
        rl.ban_reason = f"Limite di {rl.count} segnalazioni superato"
        rl.banned_until = now + timedelta(days=1)
        db.commit()

    return rl

def check_and_increment_rate_limit__(db: Session, user_id: int, limit: int = 5) -> UserRateLimit:
    """
    Controlla il rate limit per l'utente.
    - Se l'utente è bannato e la scadenza non è passata -> 403
    - Se il contatore attuale >= limit -> 429
    - Altrimenti incrementa il contatore e salva, restituisce l'oggetto.
    """
    rl = db.query(UserRateLimit).filter(UserRateLimit.user_id == user_id).first()
    now = datetime.utcnow()

    # Controlla ban attivo
    if rl and rl.is_banned and rl.banned_until and rl.banned_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Utente bannato fino al {rl.banned_until}. Motivo: {rl.ban_reason}"
        )

    # Se non esiste record, lo creiamo con count=0
    if not rl:
        rl = UserRateLimit(user_id=user_id, count=0)
        db.add(rl)
        db.commit()

    # Controlla limite già raggiunto
    if rl.count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Hai superato il limite di {limit} segnalazioni. Riprova più tardi."
        )

    # Incrementa contatore
    rl.count += 1
    db.add(rl)
    db.commit()

    # Se ha raggiunto il limite, banna automaticamente (opzionale)
    if rl.count == limit:
        rl.is_banned = True
        rl.ban_reason = f"Limite di {limit} segnalazioni superato"
        rl.banned_until = now + timedelta(days=1)
        db.commit()

    return rl
