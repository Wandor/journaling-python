from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models import Password
from app.db.session import get_db
from loguru import logger

async def deactivate_expired_passwords():
    db: Session = next(get_db())
    now = datetime.utcnow()

    try:
        expired_passwords = db.query(Password).filter(
            Password.password_expiry < now,
            Password.is_active.is_(True)
        ).all()

        if not expired_passwords:
            logger.info("No expired passwords to deactivate.")
            return

        for password in expired_passwords:
            password.is_active = False
            logger.info(f"Deactivated password for userId={password.userId}")

        db.commit()
    except Exception as e:
        logger.error(f"Failed to deactivate expired passwords: {e}")
    finally:
        db.close()
