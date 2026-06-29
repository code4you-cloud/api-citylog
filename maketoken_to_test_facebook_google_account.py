import datetime
from jose import JWTError, jwt

secret = "ju1rzFL2SsuqjWJta_JHdEwjZLly4RyTXKocHB7kpvw"
payload = {
    "id": 21,                    # user_id dell'utente social
    "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
