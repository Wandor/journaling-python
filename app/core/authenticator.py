import jwt

from datetime import datetime

from fastapi import Request, HTTPException, status, Depends

from jose import  jwt

from typing import List

from app.core.config import settings
from app.core.logger import logger

JWT_SECRET = settings.JWT_SECRET
ALGORITHM = "HS256"


class AuthenticatedUser:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role

async def authenticate_user(request: Request) -> AuthenticatedUser:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    token = auth_header.split(" ")[1]


    # Check token segments
    if len(token.split('.')) != 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token format")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM], options={"verify_exp": False})


        # Validate expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcfromtimestamp(exp_timestamp) < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

        # Extract user info
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        return AuthenticatedUser(user_id=user_id, role=role)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

def authorize(roles: List[str]):
    def dependency(user: AuthenticatedUser = Depends(authenticate_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return user
    return dependency
