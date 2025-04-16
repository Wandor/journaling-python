import random
import string
import jwt
import uuid

from fastapi import HTTPException, status

from datetime import datetime, timedelta

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.db.models import User, Password, UserPreferences

from app.core.config import settings
from app.core.redis_helper import RedisHelper

from app.schemas.auth import LoginSchema, VerifyOTPSchema, UserIdSchema, ResetPasswordSchema

from app.utils.security import hash_password, verify_password

def create_jwt_token(user_id: uuid.UUID, role: str):
    expiration_time = datetime.now() + timedelta(seconds=settings.JWT_EXPIRATION)

    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": expiration_time
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def generate_otp(length=6):
    otp = ''.join(random.choices(string.digits, k=length))
    return otp


async def login(db: AsyncSession, data: LoginSchema, ip_address: str):
    password = data.password

    result = await db.execute(select(User).filter_by(email_address=data.emailAddress))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    if not user.status or user.is_locked_out:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account locked! Contact our help desk")

    result = await db.execute(select(Password).filter_by(user_id=user.id))
    user_password = result.scalars().first()

    if not user_password or not verify_password(user_password.password, password):
        user.access_failed_count += 1
        if user.access_failed_count >= settings.ACCOUNT_LOCK_MAX_COUNT:
            user.is_locked_out = True
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials!")

    if user_password.password_expiry < datetime.now():
        user_password.is_active = False
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password expired!")

    current_date = datetime.now()

    result = await db.execute(select(UserPreferences).filter_by(user_id=user.id))
    user_preferences = result.scalars().first()
    two_factor_enabled = user_preferences.two_factor_enabled if user_preferences else False

    otp = ''
    otp_verified = False

    if two_factor_enabled:
        # Calculate hours passed since last OTP resend
        last_resend_timestamp = user.last_otp_resend_date or datetime(1970, 1, 1)
        if isinstance(last_resend_timestamp, str):
            last_resend_timestamp = datetime.fromisoformat(last_resend_timestamp)

        hours_passed_after_last_otp = abs((datetime.now() - last_resend_timestamp).total_seconds()) / 3600

        if user.otp_resend_count >= int(settings.OTP_RESEND_MAX_COUNT) and hours_passed_after_last_otp < int(settings.OTP_SEND_MAX_HOURS):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too Many OTP requests, try again later!")

        # Generate and update OTP
        otp = generate_otp(6)
        user.otp_resend_count += 1
        user.otp_sent = True
        user.last_otp_resend_date = current_date
        await db.commit()

    hashed_otp = hash_password(otp)

    refresh_token = str(uuid.uuid4())
    token = create_jwt_token(user.id, user.role.value)

    session_obj = {
        'otpValue': hashed_otp if two_factor_enabled else None,
        'otpVerified': otp_verified,
        'otpExpiry': (current_date + timedelta(minutes=int(settings.OTP_EXPIRY_MINUTES))).isoformat(),
        'refreshToken': refresh_token,
        'refreshTokenExpiry': (current_date + timedelta(minutes=int(settings.JWT_REFRESH_EXPIRATION))).isoformat(),
        'userId': str(user.id),
        'sessionStart': current_date.isoformat(),
        'sessionEnd': None,
        'sessionAddress': ip_address,
        'sessionStatus': True,
    }

    # Store session in Redis
    await RedisHelper.redis_set(
        key="session",
        value=session_obj,
        expiry=86400,
        data_actions={
            "setAsArray": False,
            "actionIfExists": "replace",
            "uniqueKey": "userId",
        }
    )

    user.last_login_date = current_date
    await db.commit()

    if two_factor_enabled:
        return {"otp": otp}, status.HTTP_200_OK

    return {"token": token, "refreshToken": refresh_token}, status.HTTP_200_OK


async def refresh_token(db: AsyncSession, user_id: str, token: str):
    key = f"session-{user_id}"
    active_session = await RedisHelper.redis_get(key)

    if not active_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active session")

    session_refresh_token = active_session.get("refreshToken")
    refresh_token_expiry = active_session.get("refreshTokenExpiry")
    session_status = active_session.get("sessionStatus")

    if not refresh_token_expiry or not session_refresh_token or not session_status:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session data")

    current_date = datetime.now()
    expiry_time = datetime.fromisoformat(refresh_token_expiry)

    if current_date >= expiry_time or not session_status:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired!")

    if token != session_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist!")

    access_token = create_jwt_token(user_id, user.role.value)

    await RedisHelper.redis_set(
        key="session",
        value=active_session,
        expiry=86400,  # 1 day
        data_actions={
            "setAsArray": False,
            "actionIfExists": "replace",
            "uniqueKey": "userId"
        }
    )

    return {
        "message": "Token generated successfully!",
        "accessToken": access_token,
        "refreshToken": session_refresh_token,
    }, status.HTTP_200_OK


async def verify_otp(db: AsyncSession, data: VerifyOTPSchema):
    user_id = data.userId
    otp_input = data.otpValue
    current_date = datetime.now()

    # Fetch session from Redis
    session_key = f"session-{user_id}"
    active_session = await RedisHelper.redis_get(session_key)

    if not active_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session")

    otp_expiry = active_session.get("otpExpiry")
    otp_value = active_session.get("otpValue")
    otp_verified = active_session.get("otpVerified")

    if otp_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="OTP already used, request for another one"
        )

    if datetime.fromisoformat(otp_expiry) < current_date:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="OTP expired!"
        )

    if not verify_password(otp_value, otp_input):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # Mark OTP as verified and update expiry
    active_session["otpVerified"] = True
    active_session["otpExpiry"] = (current_date + timedelta(minutes=int(settings.OTP_EXPIRY_MINUTES))).isoformat()

    await RedisHelper.redis_set(
        key="session",
        value=active_session,
        expiry=86400,
        data_actions={
            "setAsArray": False,
            "actionIfExists": "replace",
            "uniqueKey": "userId",
        }
    )

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()
    if user:
        user.otp_resend_count += 1
        user.otp_sent = True
        user.last_otp_resend_date = current_date
        await db.commit()

    return {
        "success": True,
        "message": "OTP Verified!",
        "status": "OK"
    }, status.HTTP_200_OK


async def resend_otp(db: AsyncSession, data: UserIdSchema):
    user_id = data.userId
    current_date = datetime.now()

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    last_resend = user.last_otp_resend_date or datetime.fromtimestamp(0)
    resend_count = user.otp_resend_count or 0
    hours_since_last_resend = abs((current_date - last_resend).total_seconds()) / 3600

    if resend_count > int(settings.OTP_RESEND_MAX_COUNT) and hours_since_last_resend < int(settings.OTP_SEND_MAX_HOURS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Surpassed Maximum Number of OTP Resends! Contact Administrator!"
        )

    # Retrieve session
    session_key = f"session-{user_id}"
    current_session = await RedisHelper.redis_get(session_key)

    if not current_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found! Log in again")

    otp = generate_otp(6)
    current_session["otpVerified"] = False
    current_session["otpValue"] = hash_password(otp)
    current_session["otpExpiry"] = (current_date + timedelta(minutes=int(settings.OTP_EXPIRY_MINUTES))).isoformat()

    await RedisHelper.redis_set(
        key="session",
        value=current_session,
        expiry=86400,
        data_actions={
            "setAsArray": False,
            "actionIfExists": "replace",
            "uniqueKey": "userId",
        }
    )

    user.otp_resend_count += 1
    user.otp_sent = True
    user.last_otp_resend_date = current_date
    await db.commit()

    return {
        "success": True,
        "message": f"Your One Time Password is: {otp}",
        "status": "OK"
    }, status.HTTP_200_OK


async def reset_password(db: AsyncSession, data: ResetPasswordSchema):
    email_address = data.emailAddress
    new_password = data.password
    current_date = datetime.now()

    result = await db.execute(select(User).filter_by(email_address=email_address))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    user_id = user.id
    hashed_password = hash_password(new_password)

    user.status = True
    user.is_locked_out = False
    user.last_password_changed_date = current_date
    await db.commit()

    expiry_date = current_date + timedelta(days=int(settings.PASSWORD_EXPIRY_DAYS))

    await db.execute(
        update(Password)
        .where(Password.user_id == user_id, Password.is_active == True)
        .values(is_active=False)
    )

    new_password_record = Password(
        user_id=user_id,
        password=hashed_password,
        password_expiry=expiry_date,
        is_active=True
    )
    db.add(new_password_record)
    await db.commit()

    return {
        "success": True,
        "message": "Password has been changed",
    }, status.HTTP_201_CREATED

async def logout_user(db: AsyncSession, data: UserIdSchema):
    user_id = data.userId

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="userId is required"
        )

    session_key = f"session-{user_id}"
    was_deleted = await RedisHelper.redis_delete(session_key)

    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already deleted"
        )

    return {
        "message": "logout successful"
    }, status.HTTP_200_OK
