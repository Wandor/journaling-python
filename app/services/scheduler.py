from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.password_service import deactivate_expired_passwords
from app.core.logger import logger

def start_cron_jobs():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        deactivate_expired_passwords,
        CronTrigger(hour=0, minute=0),
        id="deactivate_expired_passwords",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Password expiry cron job scheduled.")
