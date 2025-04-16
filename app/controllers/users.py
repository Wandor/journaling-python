from app.core.config import settings

from app.db.models import User, Password, UserPreferences

from app.schemas.user import RegisterUser, UserPreference

from app.utils.security import hash_password

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from datetime import datetime, timedelta
from fastapi import HTTPException, status

async def register_user(db: AsyncSession, data: RegisterUser):
    # Check if the user already exists
    existing_user = await db.execute(select(User).filter_by(email_address=data.emailAddress))
    existing_user = existing_user.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # Hash the password and set the password expiry date
    hashed_pw = hash_password(data.password)
    now = datetime.now()
    expiry_date = now + timedelta(days=settings.PASSWORD_EXPIRY_DAYS)

    # Create a new user
    new_user = User(
        user_name=data.userName,
        first_name=data.firstName,
        last_name=data.lastName,
        email_address=data.emailAddress,
        mobile_number=data.mobileNumber,
        role=data.role,
        last_password_changed_date=now,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Create the password entry for the new user
    password_entry = Password(
        user_id=new_user.id,
        password=hashed_pw,
        password_expiry=expiry_date,
        is_active=True,
    )
    db.add(password_entry)
    await db.commit()

    # Set up user preferences (defaulting to two_factor_enabled=False)
    preferences = UserPreferences(
        user_id=new_user.id,
        two_factor_enabled=False
    )
    db.add(preferences)
    await db.commit()

    return {"message": "User registered successfully"}, status.HTTP_201_CREATED

async def upsert_user_preferences(db: AsyncSession, user_id: UUID, data: UserPreference):
    # Check if the preferences already exist
    result = await db.execute(select(UserPreferences).filter(UserPreferences.user_id == user_id))
    existing = result.scalar_one_or_none()

    if existing:
        # Update the existing preferences
        for field, value in data.dict().items():
            setattr(existing, field, value)
    else:
        # Create new preferences if they don't exist
        existing = UserPreferences(user_id=user_id, **data.dict())

    db.add(existing)
    await db.commit()
    await db.refresh(existing)

    return {"message": "Preferences successfully updated!", "preferences": existing}, status.HTTP_200_OK