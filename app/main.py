import os
from fastapi import FastAPI, APIRouter
import asyncio

from app.configs.rate_limiter import limiter
from app.configs.redis_config import get_redis_client
from app.core.rabbitmq import RabbitMQ
from fastapi.exceptions import RequestValidationError

from app.core.error_handler import validation_exception_handler
from app.core.logger import logger, configure_loguru
from app.routes import users, auth, journal
from app.services.journal_worker import rabbitmq_handler
from app.services.scheduler import start_cron_jobs
from slowapi import  _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from slowapi.middleware import SlowAPIMiddleware



# Initialize FastAPI app
app = FastAPI()



app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.add_exception_handler(RequestValidationError, validation_exception_handler)

api_router = APIRouter(prefix="/api/v1")


app.include_router(users.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(journal.router, prefix="/api/v1")

app.include_router(api_router)


configure_loguru()

rabbitmq = RabbitMQ("amqp://localhost")


@app.on_event("startup")
async def startup_event():
    try:
        # Redis connection check
        redis = await get_redis_client()
        await redis.ping()
        logger.info("Redis connected on startup.")

        # Start cron jobs
        start_cron_jobs()

        # RabbitMQ connection check
        await rabbitmq.connect()
        await rabbitmq.channel.declare_queue("health_check_queue", durable=True)
        logger.info("RabbitMQ connected on startup.")

        asyncio.create_task(
            rabbitmq.consume("entry_queue", rabbitmq_handler)
        )

    except Exception as e:
        logger.error(f"Startup error: {e}")




def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 4000)))


if __name__ == "__main__":
    main()
