# API Citylog - Guida Completa ai Comandi CURL

## Introduzione

Questa guida fornisce una panoramica completa degli endpoint dell'API Citylog, basata su FastAPI. L'API gestisce autenticazione, utenti, servizi urbani (rifiuti, tronchi, censimento, piantumazioni, strade) e sottoscrizioni, con un agente AI per suggerimenti. 

**Base URL**: `http://192.168.1.159:8000`

**Autenticazione**: 
- Endpoint di lettura (es. `/rifiuti`, `/tronchi`, ecc.) usano un token API statico passato come header `X-API-Key`.
- Endpoint di scrittura o gestione utenti/sottoscrizioni richiedono un token JWT ottenuto via `/auth/token` con `Authorization: Bearer <token>`.

**Rate Limiting**: Endpoint di lettura limitati a 1000 chiamate/giorno per IP (configurabile con `slowapi`).

**Headers Comuni**:
- `Content-Type: application/json` per body JSON.
- `X-API-Key: <api_key>` per endpoint di lettura (es. `/rifiuti`).
- `Authorization: Bearer <token>` per endpoint autenticati.

**Errori Comuni**:
- `401 Unauthorized`: Token API o JWT non valido/mancante.
- `404 Not Found`: Risorsa non trovata.
- `429 Too Many Requests`: Limite di chiamate giornaliero superato.
- `500 Internal Server Error`: Errore server.

**Requisiti**:
- Installa `curl` (`sudo apt-get install curl` su Linux, `brew install curl` su macOS).
- Sostituisci `<api_key>`, `<token>`, `<username>`, `<password>` con valori reali.
- Token API: Usa `python -c "import uuid; print(uuid.uuid4())"` per generare un token (es. `your-api-key`).

## Autenticazione

### Ottenere il Token JWT
**Descrizione**: Autentica l'utente e restituisce un token JWT per operazioni protette (es. gestione utenti, sottoscrizioni).

**Metodo**: POST  
**URL**: `/auth/token`  
**Headers**: `Content-Type: application/x-www-form-urlencoded`  
**Body**: `username=<username>&password=<password>`  
**Risposta**: `200 OK` con `{ "access_token": "<token>", "token_type": "bearer" }`

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"
```

**Risposta Esempio**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Note**:
- Token scade in 60 minuti.
- Per refresh, usa `/auth/refresh` (se implementato) o rieffettua il login.

## Endpoint Utenti (Users)

### Elenca Utenti
**Descrizione**: Recupera la lista di tutti gli utenti registrati. Richiede privilegi admin.

**Metodo**: GET  
**URL**: `/users/`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di utenti `{ id, username, email }`.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/users/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  {
    "id": 2,
    "username": "user1",
    "email": "user1@example.com"
  }
]
```

### Crea Utente
**Descrizione**: Crea un nuovo utente. Richiede privilegi admin.

**Metodo**: POST  
**URL**: `/users/`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "username": "<username>", "password": "<password>", "email": "<email>" }`  
**Risposta**: `201 Created` con utente creato.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/users/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "newpass", "email": "newuser@example.com"}'
```

**Risposta Esempio**:
```json
{
  "id": 3,
  "username": "newuser",
  "email": "newuser@example.com"
}
```

### Ottieni Utente per ID
**Descrizione**: Recupera i dettagli di un utente specifico.

**Metodo**: GET  
**URL**: `/users/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con dettagli utente.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/users/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com"
}
```

### Aggiorna Utente
**Descrizione**: Aggiorna i dati di un utente esistente.

**Metodo**: PUT  
**URL**: `/users/{user_id}`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "username": "<new_username>", "email": "<new_email>" }`  
**Risposta**: `200 OK` con utente aggiornato.

**Esempio CURL**:
```bash
curl -X PUT "http://192.168.1.159:8000/users/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"username": "updatedadmin", "email": "updatedadmin@example.com"}'
```

### Elimina Utente
**Descrizione**: Elimina un utente. Richiede privilegi admin.

**Metodo**: DELETE  
**URL**: `/users/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `204 No Content`.

**Esempio CURL**:
```bash
curl -X DELETE "http://192.168.1.159:8000/users/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Endpoint Rifiuti

### Elenca Rifiuti
**Descrizione**: Recupera tutti i record con `typo == "rifiuti"`. Accessibile con token API statico, limitato a 1000 chiamate/giorno per IP.

**Metodo**: GET  
**URL**: `/rifiuti/`  
**Headers**: `X-API-Key: <api_key>`  
**Risposta**: `200 OK` con array di record `{ lat, lon, address, data, image_url }`.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/rifiuti/" \
  -H "X-API-Key: your-api-key"
```

**Risposta Esempio**:
```json
[
  {
    "lat": 45.5210772,
    "lon": 10.21249526,
    "address": "Via Esempio 123",
    "data": "2023-10-01",
    "image_url": "https://example.com/image.jpg"
  }
]
```

**Note**:
- Limite: 1000 chiamate/giorno per IP.
- Errori: `401` (token non valido), `429` (limite superato).

### Crea Record Rifiuti
**Descrizione**: Crea un nuovo record rifiuti. Richiede autenticazione utente.

**Metodo**: POST  
**URL**: `/rifiuti/`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "lat": <lat>, "lon": <lon>, "address": "<address>", "data": "<data>", "image_url": "<image_url>" }`  
**Risposta**: `201 Created` con record creato.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/rifiuti/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"lat": 45.5210772, "lon": 10.21249526, "address": "Via Nuova", "data": "2023-10-02", "image_url": "https://example.com/new.jpg"}'
```

### Ottieni Record Rifiuti per ID
**Descrizione**: Recupera un record rifiuti specifico.

**Metodo**: GET  
**URL**: `/rifiuti/{record_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con record.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/rifiuti/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Aggiorna Record Rifiuti
**Descrizione**: Aggiorna un record rifiuti esistente.

**Metodo**: PUT  
**URL**: `/rifiuti/{record_id}`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "lat": <lat>, "lon": <lon>, "address": "<address>", "data": "<data>", "image_url": "<image_url>" }`  
**Risposta**: `200 OK` con record aggiornato.

**Esempio CURL**:
```bash
curl -X PUT "http://192.168.1.159:8000/rifiuti/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"lat": 45.5210772, "lon": 10.21249526, "address": "Via Aggiornata", "data": "2023-10-03", "image_url": "https://example.com/updated.jpg"}'
```

### Elimina Record Rifiuti
**Descrizione**: Elimina un record rifiuti.

**Metodo**: DELETE  
**URL**: `/rifiuti/{record_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `204 No Content`.

**Esempio CURL**:
```bash
curl -X DELETE "http://192.168.1.159:8000/rifiuti/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Endpoint Tronchi

### Elenca Tronchi
**Descrizione**: Recupera tutti i record con `typo == "tronchi"`. Accessibile con token API, limitato a 1000 chiamate/giorno per IP.

**Metodo**: GET  
**URL**: `/tronchi/`  
**Headers**: `X-API-Key: <api_key>`  
**Risposta**: `200 OK` con array di record `{ lat, lon, address, data, image_url }`.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/tronchi/" \
  -H "X-API-Key: your-api-key"
```

**Risposta Esempio**:
```json
[
  {
    "lat": 45.522,
    "lon": 10.213,
    "address": "Via Tronchi 456",
    "data": "2023-10-04",
    "image_url": "https://example.com/tronchi.jpg"
  }
]
```

**Note**: Simile a `/rifiuti/`. CRUD (POST, GET/{id}, PUT/{id}, DELETE/{id}) seguono lo stesso pattern di `/rifiuti/`.

## Endpoint Censimento

### Elenca Censimento
**Descrizione**: Recupera tutti i record con `typo == "censimento"`. Accessibile con token API.

**Metodo**: GET  
**URL**: `/censimento/`  
**Headers**: `X-API-Key: <api_key>`  
**Risposta**: `200 OK` con array di record.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/censimento/" \
  -H "X-API-Key: your-api-key"
```

**Note**: CRUD simili a `/rifiuti/`.

## Endpoint Piantumazioni

### Elenca Piantumazioni
**Descrizione**: Recupera tutti i record con `typo == "piantumazioni"`. Accessibile con token API.

**Metodo**: GET  
**URL**: `/piantumazioni/`  
**Headers**: `X-API-Key: <api_key>`  
**Risposta**: `200 OK` con array di record.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/piantumazioni/" \
  -H "X-API-Key: your-api-key"
```

## Endpoint Strade

### Elenca Strade
**Descrizione**: Recupera tutti i record con `typo == "strade"`. Accessibile con token API.

**Metodo**: GET  
**URL**: `/strade/`  
**Headers**: `X-API-Key: <api_key>`  
**Risposta**: `200 OK` con array di record.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/strade/" \
  -H "X-API-Key: your-api-key"
```

## Endpoint Subscriptions (Sottoscrizioni)

### Elenca Sottoscrizioni per Utente
**Descrizione**: Recupera le sottoscrizioni di un utente specifico. Richiede autenticazione.

**Metodo**: GET  
**URL**: `/subscriptions/user/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di sottoscrizioni `{ id, user_id, name, cost, periodicity, start_date, end_date, status }`.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/subscriptions/user/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "Netflix",
    "cost": 9.99,
    "periodicity": "monthly",
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "status": "active"
  }
]
```

### Crea Sottoscrizione
**Descrizione**: Crea una nuova sottoscrizione per un utente.

**Metodo**: POST  
**URL**: `/subscriptions/`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "user_id": <user_id>, "name": "<name>", "cost": <cost>, "periodicity": "<periodicity>", "start_date": "<date>", "end_date": "<date>", "status": "<status>" }`  
**Risposta**: `201 Created` con sottoscrizione creata.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/subscriptions/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Spotify", "cost": 10.99, "periodicity": "monthly", "start_date": "2023-10-01", "end_date": "2023-12-31", "status": "active"}'
```

### Aggiorna Sottoscrizione
**Descrizione**: Aggiorna una sottoscrizione esistente.

**Metodo**: PUT  
**URL**: `/subscriptions/{subscription_id}`  
**Headers**: `Authorization: Bearer <token>`, `Content-Type: application/json`  
**Body**: `{ "name": "<name>", "cost": <cost>, "periodicity": "<periodicity>", "start_date": "<date>", "end_date": "<date>", "status": "<status>" }`  
**Risposta**: `200 OK` con sottoscrizione aggiornata.

**Esempio CURL**:
```bash
curl -X PUT "http://192.168.1.159:8000/subscriptions/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Spotify Premium", "cost": 12.99, "periodicity": "monthly", "start_date": "2023-10-01", "end_date": "2024-12-31", "status": "active"}'
```

### Elimina Sottoscrizione
**Descrizione**: Elimina una sottoscrizione.

**Metodo**: DELETE  
**URL**: `/subscriptions/{subscription_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `204 No Content`.

**Esempio CURL**:
```bash
curl -X DELETE "http://192.168.1.159:8000/subscriptions/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Report Sottoscrizioni
**Descrizione**: Genera un report dei costi delle sottoscrizioni per periodicità.

**Metodo**: GET  
**URL**: `/subscriptions/report/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array `{ periodicity, total_cost }`.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/subscriptions/report/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
[
  {
    "periodicity": "monthly",
    "total_cost": 20.98
  },
  {
    "periodicity": "yearly",
    "total_cost": 99.99
  }
]
```

## Endpoint AI Agent

### Genera Promemoria
**Descrizione**: Genera promemoria per scadenze di sottoscrizioni.

**Metodo**: POST  
**URL**: `/ai-agent/reminders/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Body**: Nessuno.  
**Risposta**: `200 OK` con array di notifiche `{ id, user_id, subscription_id, message, type, created_at }`.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/ai-agent/reminders/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "subscription_id": 1,
    "message": "Netflix scade tra 3 giorni",
    "type": "reminder",
    "created_at": "2023-10-01T12:00:00"
  }
]
```

### Genera Suggerimenti
**Descrizione**: Genera suggerimenti di risparmio basati su sottoscrizioni.

**Metodo**: POST  
**URL**: `/ai-agent/suggestions/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di notifiche.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/ai-agent/suggestions/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Risposta Esempio**:
```json
[
  {
    "id": 2,
    "user_id": 1,
    "subscription_id": 1,
    "message": "Passa a Netflix Standard per risparmiare 2.99 €/mese",
    "type": "suggestion",
    "created_at": "2023-10-01T12:01:00"
  }
]
```

### Auto-Cancellazione
**Descrizione**: Cancella automaticamente sottoscrizioni scadute.

**Metodo**: POST  
**URL**: `/ai-agent/auto-cancel/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di notifiche.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/ai-agent/auto-cancel/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Sync Citylog
**Descrizione**: Genera suggerimenti basati su dati Citylog (es. ottimizzazione raccolta rifiuti).

**Metodo**: POST  
**URL**: `/ai-agent/citylog-sync/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di notifiche.

**Esempio CURL**:
```bash
curl -X POST "http://192.168.1.159:8000/ai-agent/citylog-sync/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Elenca Notifiche
**Descrizione**: Recupera tutte le notifiche generate dall'AI per un utente.

**Metodo**: GET  
**URL**: `/ai-agent/notifications/{user_id}`  
**Headers**: `Authorization: Bearer <token>`  
**Risposta**: `200 OK` con array di notifiche.

**Esempio CURL**:
```bash
curl -X GET "http://192.168.1.159:8000/ai-agent/notifications/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Note Utili

### Rate Limiting
- **Limite**: 1000 chiamate/giorno per IP su endpoint di lettura (`/rifiuti`, `/tronchi`, ecc.).
- **Errore 429**: Se superato, attendi il reset (24 ore) o usa un token API diverso (se configurato per token).
- **Configurazione**: Modifica in FastAPI con `@limiter.limit("1000/day")`. Per limite per token:
  ```python
  limiter = Limiter(key_func=lambda request: request.headers.get("X-API-Key", "no-key"))
  ```

### Token API
- **Generazione**: Crea un token con `python -c "import uuid; print(uuid.uuid4())"`.
- **Sicurezza**: Conserva il token in un luogo sicuro. In produzione, usa un database per gestire token per-cliente.
- **Esempio**: Sostituisci `your-api-key` con il valore configurato in `rifiuti.py` (es. `VALID_API_KEY`).

### Debug e Monitoraggio
- **Log FastAPI**: Abilita logging dettagliato (`logging.basicConfig(level=logging.DEBUG)`) per tracciare errori e chiamate.
- **Console Browser**: Per il template Leaflet (`sample_keaflt_mono5.html`), usa la console (F12) per errori fetch (`401`, `429`).
- **Test Multipli**:
  ```bash
  API_KEY="your-api-key"
  for i in {1..5}; do
    curl -H "X-API-Key: $API_KEY" http://192.168.1.159:8000/rifiuti/
  done
  ```

### Integrazione con Template Leaflet
- Il template `sample_keaflt_mono5.html` usa `X-API-Key` per chiamare `/rifiuti`, `/tronchi`, ecc.
- Assicurati che `API_KEY` nel template corrisponda a `VALID_API_KEY` in `rifiuti.py`.
- Risposta attesa: Array di oggetti `{ lat, lon, address, data, image_url }`.

### Preparazione per SaaS di Abbonamenti
- **Campi Sottoscrizioni**: Aggiungi `subscription_cost`, `periodicity`, `expiration_date` a `/rifiuti` per visualizzarli nel popup:
  ```javascript
  // In sample_keaflt_mono5.html
  popupContent += `
      <div class="popup-field">
          <span class="popup-label">Costo:</span>
          <span class="popup-value">${markerData.subscription_cost || 'N/A'} €/mese</span>
      </div>
  `;
  ```
- **Endpoint Token Dinamico**: Crea `/auth/api-key` per generare token per-cliente.
- **Rate Limiting per Cliente**: Configura limiti diversi per livelli di abbonamento (es. 5000/giorno per premium).

### Risorse
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SlowAPI Docs**: https://slowapi.readthedocs.io/
- **CURL Manual**: https://curl.se/docs/manpage.html
- **Generatore UUID**: `python -c "import uuid; print(uuid.uuid4())"`

### Errori Comuni e Soluzioni
- **401 Unauthorized**: Verifica `X-API-Key` o `Authorization` header.
- **429 Too Many Requests**: Attendi il reset del limite giornaliero.
- **500 Internal Server Error**: Controlla log FastAPI per errori di database o configurazione.
- **CORS Error**: Configura `allow_origins` in `CORSMiddleware` per il dominio frontend.

Per ulteriori dettagli o supporto, contatta il team di sviluppo o verifica i log server.