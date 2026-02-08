from faststream.kafka import KafkaBroker

BROKER_URL = "redpanda:9092"

broker = KafkaBroker(BROKER_URL)

async def publish_event(topic: str, data: dict):
    async with broker:
        await broker.publish(
            data,
            topic=topic
        )
