from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")


def create_hash(password: str):
    return pwd_context.hash(password)

def verify_hash(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
