from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user_rate_limit import UserRateLimit

def check_and_increment_rate_limit(db: Session, user_id: int, limit: int = 5) -> UserRateLimit:
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
