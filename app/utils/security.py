from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

pwd_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        assert isinstance(hashed_password, str), "hashed_password must be a string"
        assert isinstance(plain_password, str), "plain_password must be a string"

        pwd_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False