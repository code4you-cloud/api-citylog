# api_citylog

**api_citylog** è un'applicazione FastAPI progettata per gestire segnalazioni geolocalizzate di problematiche ambientali, stradali e di rifiuti, con un'interfaccia API RESTful sicura e scalabile. Il progetto consente agli utenti autenticati di creare, visualizzare, aggiornare ed eliminare segnalazioni, con supporto per dati storici privi di associazione utente e integrazione di dati esterni (es. prezzi del Brent).

## Finalità del Progetto
L'obiettivo principale di **api_citylog** è fornire un sistema centralizzato per:
- **Segnalazioni geolocalizzate**: Raccogliere e gestire segnalazioni di rifiuti, problemi ambientali e stradali, con informazioni su posizione, immagini e stato.
- **Accesso controllato**: Garantire che solo utenti autenticati possano interagire con le segnalazioni, mantenendo la possibilità di accedere a dati storici non associati a utenti specifici.
- **Integrazione dati esterni**: Recuperare informazioni da API esterne (es. prezzi del Brent) per analisi correlate.
- **Tracciabilità e manutenzione**: Offrire un sistema robusto con logging e rate limiting per monitorare le operazioni e prevenire abusi.

Il progetto è pensato per enti locali, cittadini o organizzazioni che necessitano di un sistema per monitorare e gestire segnalazioni ambientali in modo strutturato.

## Caratteristiche Principali
- **Autenticazione JWT**: Accesso sicuro tramite token JWT per autenticare gli utenti, con supporto per creazione utenti e login (`POST /users/`, `POST /auth/token`).
- **Gestione segnalazioni**:
  - **Creazione** (`POST /rifiuti/`, `/ambiente/`, `/strade/`): Inserimento di segnalazioni con dati geolocalizzati, immagini e stato.
  - **Lettura** (`GET /rifiuti/`, `/ambiente/`, `/strade/`): Recupero delle segnalazioni per l'utente autenticato o di tutti i dati con `user_id` vuoto.
  - **Aggiornamento** (`PUT /rifiuti/{id}`, `/ambiente/{id}`, `/strade/{id}`): Modifica parziale dei dati (es. stato, posizione), con aggiornamento automatico del timestamp (`image_time`).
  - **Eliminazione** (`DELETE /rifiuti/{id}`, `/ambiente/{id}`, `/strade/{id}`): Rimozione delle segnalazioni, con autorizzazione basata su `user_id`.
- **Database PostgreSQL**: Persistenza dei dati nella tabella `emails_emaildata`, con modello `EmailData` che supporta `user_id` opzionale (`NULL`) per compatibilità con dati storici.
- **Integrazione API esterne**: Endpoint `/brent/` per recuperare dati sui prezzi del Brent (es. tramite API esterne come Alpha Vantage).
- **Rate Limiting**: Limite di 100 richieste al minuto per prevenire abusi, implementato tramite middleware personalizzato.
- **Logging**: Tracciamento delle operazioni (`POST`, `GET`, `PUT`, `DELETE`) in un file `app.log` e sulla console, con dettagli su utente, ID record ed esito.
- **Documentazione interattiva**: Interfaccia Swagger disponibile su `/docs` per testare gli endpoint.

## Tecnologie Utilizzate
- **FastAPI**: Framework Python per API RESTful ad alte prestazioni.
- **SQLAlchemy**: ORM per la gestione del database PostgreSQL.
- **Pydantic**: Validazione dei dati per input e output (schemi `EmailData`, `EmailDataCreate`, `EmailDataUpdate`).
- **Passlib (bcrypt)**: Hashing sicuro delle password per l'autenticazione.
- **JWT**: Autenticazione basata su token con scadenza (30 minuti).
- **Httpx**: Client HTTP asincrono per chiamate ad API esterne (es. Brent).
- **Python Logging**: Registrazione delle operazioni per monitoraggio e debug.

## Prerequisiti
- **Python**: 3.12 o 3.13 (3.12 consigliato per compatibilità con `bcrypt`).
- **PostgreSQL**: Database configurato (es. `postgresql://user:password@localhost:5432/db_name`).
- **Dipendenze**: Installa con `pip install -r requirements.txt`.
- **Strumenti consigliati**:
  - `jq` per formattare output JSON nel terminale.
  - Compilatore C (es. `gcc`) per installare `bcrypt` su macOS/Linux.

## Installazione
1. Clona il repository:
   ```bash
   git clone <repository_url>
   cd api_citylog
   ```
2. Crea e attiva un ambiente virtuale:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Su Windows: .venv\Scripts\activate
   ```
3. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura il database in `app/db/database.py` (es. URL PostgreSQL).
5. Avvia il server:
   ```bash
   ./start.sh
   ```
6. Accedi alla documentazione Swagger: `http://localhost:8000/docs` (o `http://192.168.1.159:3000/docs` se deployato).

## Utilizzo
### Autenticazione
1. **Crea un utente**:
   ```bash
   curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "securepassword123", "name": "Test User"}' | jq
   ```
2. **Login e ottieni token JWT**:
   ```bash
   curl -X POST "http://localhost:8000/auth/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=test@example.com&password=securepassword123" | jq
   ```

### Gestione Segnalazioni
- **Crea segnalazione** (es. rifiuti):
  ```bash
  curl -X POST "http://localhost:8000/rifiuti/" -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"latitude": "45.5245", "longitude": "10.2188", "city": "Brescia", "address": "Via S. Zeno, 102", "image_id": "img123", "image_url": "/media/img.jpg", "image_file": "img.jpg", "status": "pending", "typo": "rifiuti"}' | jq
  ```
- **Recupera segnalazioni**:
  ```bash
  curl -X GET "http://localhost:8000/rifiuti/" -H "Authorization: Bearer <token>" | jq
  ```
- **Aggiorna segnalazione** (es. ID 230):
  ```bash
  curl -X PUT "http://localhost:8000/rifiuti/230" -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"status": "completato"}' | jq
  ```
- **Elimina segnalazione**:
  ```bash
  curl -X DELETE "http://localhost:8000/rifiuti/230" -H "Authorization: Bearer <token>"
  ```

### Dati Esterni
- **Recupera dati Brent**:
  ```bash
  curl -X GET "http://localhost:8000/brent/" -H "Authorization: Bearer <token>" | jq
  ```

## Struttura del Progetto
```
api_citylog/
├── app/
│   ├── db/
│   │   └── database.py          # Configurazione database PostgreSQL
│   ├── models/
│   │   ├── citylog.py          # Modello SQLAlchemy per emails_emaildata
│   │   ├── user.py             # Modello SQLAlchemy per users
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── emaildata.py        # Schemi Pydantic per segnalazioni
│   │   ├── user.py             # Schemi Pydantic per utenti
│   │   └── __init__.py
│   ├── routers/
│   │   ├── auth.py             # Endpoint per autenticazione
│   │   ├── users.py            # Endpoint per gestione utenti
│   │   ├── rifiuti.py          # Endpoint per segnalazioni rifiuti
│   │   ├── ambiente.py         # Endpoint per segnalazioni ambientali
│   │   ├── strade.py           # Endpoint per segnalazioni stradali
│   │   ├── brent.py            # Endpoint per dati Brent
│   │   └── __init__.py
│   ├── auth/
│   │   ├── dependencies.py     # Dipendenze per autenticazione JWT
│   │   ├── jwt_handler.py      # Gestione token JWT
│   │   └── security.py         # Hashing delle password
│   ├── middlewares/
│   │   └── rate_limiter.py     # Middleware per rate limiting
│   ├── logging_config.py        # Configurazione del logging
│   └── main.py                 # Entry point dell'applicazione
├── requirements.txt            # Dipendenze Python
├── start.sh                   # Script per avviare il server
└── app.log                    # File di log delle operazioni
```

## Note
- **Rate Limiting**: 100 richieste/minuto per utente, configurabile in `app/middlewares/rate_limiter.py`.
- **Logging**: Operazioni tracciate in `app.log` e sulla console (es. creazione, aggiornamento, eliminazione).
- **Compatibilità**: Usa Python 3.12 per evitare problemi con `bcrypt` su Python 3.13.
- **Dati storici**: Gli endpoint `GET` restituiscono record con `user_id` vuoto per compatibilità con dati preesistenti.

## Contributi
Per contribuire, crea una pull request con modifiche documentate. Esegui test con `pytest` e verifica la documentazione Swagger.

## Licenza
MIT License