from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.schemas.user import RegisterUser, UserPreference
from app.controllers import users as crud
from app.db.session import get_db
from uuid import UUID

router = APIRouter(prefix="/user", tags=["Users"])

@router.post("/register")
async def register_user(data: RegisterUser, db: AsyncSession = Depends(get_db)):
    result, code = await crud.register_user(db, data)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/preferences/{user_id}")
async def update_preferences(user_id: UUID, data: UserPreference, db: AsyncSession = Depends(get_db)):
    result, code = await crud.upsert_user_preferences(db, user_id, data)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


