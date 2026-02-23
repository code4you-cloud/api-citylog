# LOGIC.md

# 🔐 Autenticazione JWT - Backend FastAPI

## 1. Mappa mentale del flusso

```
Android / curl
      |
      |  (email + password)
      v
POST /auth/token  ---> routers/auth.py
      |
      | verifica password su DB
      v
create_access_token()  ---> auth/jwt_handler.py
      |
      | firma con SECRET_KEY
      v
JWT firmato
      |
      |-----------------------------------|
                                          |
                              chiamate protette
                                          |
                                          v
                                 Authorization: Bearer <token>
                                          |
                                          v
                                  get_current_user()
                                  auth/dependencies.py
                                          |
                                          | verifica firma con
                                          | la STESSA SECRET_KEY
                                          v
                                    payload utente
                                          |
                                          v
                               router (es: rifiuti.py)
```

## 2. Creazione del token

File: `routers/auth.py`

```python
access_token = create_access_token(
    data={
        "id": user.id,
        "username": user.username,
        "email": user.email
    }
)
```

Il token contiene `id`, `username` e `email`.


### Firma

File: `app/auth/jwt_handler.py`

```python
encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

- `SECRET_KEY` deve essere identica a quella usata nella decodifica
- Algoritmo: HS256

## 3. Decodifica e autenticazione

File: `auth/dependencies.py`

```python
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

- Se la secret è diversa: `JWT ERROR -> Signature verification failed`

## 4. Endpoint protetti

Nei router, ad esempio `rifiuti.py`:

```python
async def create_rifiuti(
    item: EmailDataCreate,
    current_user: dict = Depends(get_current_user),
```

- FastAPI estrae il token dall'header `Authorization: Bearer ...`
- Chiama `get_current_user()`
- Inserisce il payload decodificato in `current_user`

### Esempio payload attuale

```json
{
    "id": 15,
    "username": "Marco",
    "email": "marco@example.com",
    "exp": 1770728046
}
```

## 5. Possibili errori comuni

- SECRET_KEY diversa tra create e verify
- Algoritmo diverso (es. HS512 vs HS256)
- Token copiato male (spazi, virgole, doppi header)
- Server non riavviato dopo aggiornamenti

## 6. Debug avanzato

```python
logger.warning(f"CURRENT USER -> {current_user}")
```
- Mostra il payload decodificato direttamente in logs

## 7. Punti di forza del sistema

- Autenticazione stateless
- User ID affidabile
- Pronto per microservizi
- Django può diventare superfluo
- Backend pronto per app mobile/public API

