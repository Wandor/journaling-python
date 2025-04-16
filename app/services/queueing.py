import asyncio
from app.core.rabbitmq import RabbitMQ

rabbitmq = RabbitMQ("amqp://localhost")

def publish_to_queue(exchange: str, queue_name: str, message_body: dict):
    asyncio.create_task(rabbitmq.publish(queue_name, message_body))
