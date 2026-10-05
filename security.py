from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidSignatureError, ExpiredSignatureError
from exceptions import SignatureError, ExpiredTokenError
from pwdlib import PasswordHash
import os
from dotenv import load_dotenv

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash(os.getenv('DUMMY_PASSWORD'))

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')


def get_hashed_password(plain_password: str):
    return password_hash.hash(plain_password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def create_token(to_encode: dict):
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidSignatureError:
        raise SignatureError()
    except ExpiredSignatureError:
        raise ExpiredTokenError()

    return payload

