import asyncio
import json
from aio_pika import connect_robust, Message, IncomingMessage, ExchangeType


from app.core.logger import logger

class RabbitMQ:
    def __init__(self, url="amqp://localhost"):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        try:
            self.connection = await connect_robust(self.url)
            self.channel = await self.connection.channel()
            logger.info("[AMQP] Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"[AMQP] Connection error: {e}")
            await asyncio.sleep(1)
            await self.connect()

    async def publish(self, queue_name: str, message_body: dict):
        if not self.channel:
            await self.connect()

        # Ensure the message body is a valid JSON string
        message_json = json.dumps(message_body)

        await self.channel.declare_queue(queue_name, durable=True)
        message = Message(body=message_json.encode())
        await self.channel.default_exchange.publish(message, routing_key=queue_name)
        logger.info(f"[AMQP] Published message to {queue_name}")

    async def consume(self, queue_name: str, callback):
        if not self.channel:
            await self.connect()
        queue = await self.channel.declare_queue(queue_name, durable=True)
        logger.info(f"[AMQP] Consuming queue: {queue_name}")
        await queue.consume(callback)
