import redis
import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit=100, window=86400):
        super().__init__(app)
        self.limit = limit
        self.window = window
        #self.requests = {}
        # SOSTITUISCI QUESTA RIGA:
        # self.requests = {}
        # CON QUESTA:
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def get_client_ip(self, request: Request) -> str:
        """Estrae IP reale del client considerando proxy"""
        forwarded_ips = request.headers.get("X-Forwarded-For")
        if forwarded_ips:
            return forwarded_ips.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/rifiuti" and request.method == "GET":
            client_ip = self.get_client_ip(request)

            # SOSTITUISCI TUTTA QUESTA SEZIONE:
            """
            now = time.time()
            if client_ip in self.requests:
                self.requests[client_ip] = [
                    ts for ts in self.requests[client_ip]
                    if ts > now - self.window
                ]
                if len(self.requests[client_ip]) >= self.limit:
                    # ... resto del codice
            self.requests.setdefault(client_ip, []).append(now)
            """

            # CON QUESTA NUOVA LOGICA REDIS:
            today = datetime.now().strftime("%Y-%m-%d")
            key = f"rate_limit:rifiuti:{client_ip}:{today}"

            try:
                current_count = self.redis_client.get(key)

                if current_count and int(current_count) >= self.limit:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Limite di {self.limit} richieste giornaliere superato",
                            "reset_time": "00:00 UTC"
                        },
                        headers={
                            "Retry-After": "86400",
                            "X-RateLimit-Limit": str(self.limit),
                            "X-RateLimit-Remaining": "0"
                        }
                    )

                # Incrementa o inizializza il contatore
                if current_count is None:
                    self.redis_client.setex(key, 86400, 1)  # 24 ore TTL
                    remaining = self.limit - 1
                else:
                    new_count = self.redis_client.incr(key)
                    remaining = self.limit - new_count

            except redis.RedisError:
                # Se Redis non funziona, passa la richiesta
                remaining = self.limit

            # RESTO DEL CODICE UGUALE
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            return response

        return await call_next(request)

#    async def dispatch(self, request: Request, call_next):
#        # Applica rate limiting solo all'endpoint rifiuti GET
#        if request.url.path == "/rifiuti" and request.method == "GET":
#            client_ip = self.get_client_ip(request)
#            now = time.time()
#
#            # Pulisce le richieste vecchie (oltre 24h)
#            if client_ip in self.requests:
#                self.requests[client_ip] = [
#                    ts for ts in self.requests[client_ip]
#                    if ts > now - self.window
#                ]
#
#                # Controlla se supera il limite
#                if len(self.requests[client_ip]) >= self.limit:
#                    remaining_time = int(self.window - (now - min(self.requests[client_ip])))
#                    return JSONResponse(
#                        status_code=429,
#                        content={
#                            "detail": f"Limite di {self.limit} richieste giornaliere superato",
#                            "reset_in_seconds": remaining_time
#                        },
#                        headers={
#                            "Retry-After": str(remaining_time),
#                            "X-RateLimit-Limit": str(self.limit),
#                            "X-RateLimit-Remaining": "0"
#                        }
#                    )
#
#            # Aggiunge la richiesta corrente
#            self.requests.setdefault(client_ip, []).append(now)
#
#            # Aggiunge header informativi alla risposta
#            response = await call_next(request)
#            remaining = self.limit - len(self.requests[client_ip])
#            response.headers["X-RateLimit-Limit"] = str(self.limit)
#            response.headers["X-RateLimit-Remaining"] = str(remaining)
#            return response
#
#        # Per tutti gli altri endpoint, passa senza rate limiting
#        return await call_next(request)

#    async def dispatch(self, request: Request, call_next):
#        client_ip = request.client.host
#        now = time.time()
#
#        # Pulisce le richieste vecchie
#        if client_ip in self.requests:
#            self.requests[client_ip] = [ts for ts in self.requests[client_ip] if ts > now - self.window]
#            if len(self.requests[client_ip]) >= self.limit:
#                return JSONResponse(
#                    status_code=429,
#                    content={"detail": "Too many requests"},
#                    headers={"Retry-After": str(self.window)}
#                )
#
#        self.requests.setdefault(client_ip, []).append(now)
#        return await call_next(request)
