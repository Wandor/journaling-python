from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession


from app.schemas.auth import LoginSchema, RefreshTokenSchema, VerifyOTPSchema, UserIdSchema, ResetPasswordSchema
from app.controllers import auth as auth
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login_route(request: Request, data: LoginSchema, db: AsyncSession = Depends(get_db)):

    # Extract IP address from the request
    ip_address = request.client.host

    result, code = await auth.login(db=db, data=data, ip_address=ip_address)


    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/refreshToken")
async def refresh_token_route(request: RefreshTokenSchema, db: AsyncSession = Depends(get_db)):

    result, code = await auth.refresh_token(db, str(request.userId), request.refreshToken)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result

@router.post("/verifyOTP")
async def verify_otp_route(request: VerifyOTPSchema, db: AsyncSession = Depends(get_db)):

    result, code = await auth.verify_otp(db, data=request)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/resendOtp")
async def resend_otp_route(request: UserIdSchema, db: AsyncSession = Depends(get_db)):

    result, code = await auth.resend_otp(db, data=request)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result

@router.post("/resetPassword")
async def resend_otp_route(request: ResetPasswordSchema, db: AsyncSession = Depends(get_db)):

    result, code = await auth.reset_password(db, data=request)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/logout")
async def logout_route(request: UserIdSchema, db: AsyncSession = Depends(get_db)):

    result, code = await auth.logout_user(db, data=request)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result