import logging
import os
from typing import Literal

from faststream import FastStream
from faststream.kafka import KafkaBroker
from opensearchpy import AsyncOpenSearch
from opensearchpy import exceptions as os_exceptions
from pydantic import BaseModel

BROKER_URL = os.getenv("BROKER_URL", "localhost:9092")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "ads"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdPayload(BaseModel):
    ad_id: int
    title: str
    description: str
    price: float
    city: str


class AdEvent(BaseModel):
    event: Literal["created", "updated", "deleted"]
    data: AdPayload

broker = KafkaBroker(BROKER_URL)
app = FastStream(broker)

os_client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)


@app.on_startup
async def setup_index():
    """Idempotent index creation"""
    try:
        exists = await os_client.indices.exists(index=INDEX_NAME)
        if not exists:
            await os_client.indices.create(index=INDEX_NAME, body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "price": {"type": "float"},
                        "city": {"type": "keyword"},
                        "ad_id": {"type": "long"}
                    }
                }
            })
            logger.info(f"OpenSearch index '{INDEX_NAME}' created")
    except Exception as e:
        logger.error(f"Failed to setup index: {e}")


@broker.subscriber("ads_events")
async def handle_ad_event(msg: AdEvent):
    """
    Handles created, updated, and deleted events.
    FastStream automatically validates 'msg' against AdEvent schema.
    """
    logger.info(f"Processing event: {msg.event} for ad_id: {msg.data.ad_id}")

    try:
        if msg.event in ("created", "updated"):
            await os_client.index(
                index=INDEX_NAME,
                id=msg.data.ad_id,
                body=msg.data.model_dump(),
                refresh=True
            )
            logger.info(f"Indexed/Updated ad {msg.data.ad_id}")

        elif msg.event == "deleted":
            try:
                await os_client.delete(index=INDEX_NAME, id=msg.data.ad_id)
                logger.info(f"Deleted ad {msg.data.ad_id}")
            except os_exceptions.NotFoundError:
                logger.warning(f"Ad {msg.data.ad_id} not found for deletion")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise e
