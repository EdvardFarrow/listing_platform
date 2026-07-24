import logging
from typing import Dict, Literal, Optional

from decouple import config 
from faststream import FastStream
from faststream.kafka import KafkaBroker
from opensearchpy import AsyncOpenSearch
from opensearchpy import exceptions as os_exceptions
from pydantic import BaseModel

BROKER_URL = config("BROKER_URL", default="localhost:9092")
OPENSEARCH_URL = config("OPENSEARCH_URL", default="http://localhost:9200")
INDEX_NAME = "vacancies"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VacancyPayload(BaseModel):
    vacancy_id: int
    title: str
    description: str
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    city: str
    attributes: Dict = {}
    location: Optional[Dict[str, float]] = None

class VacancyEvent(BaseModel):
    event: Literal["created", "updated", "deleted"]
    data: VacancyPayload

broker = KafkaBroker(BROKER_URL)
app = FastStream(broker)

os_client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)

@app.on_startup
async def setup_index():
    try:
        exists = await os_client.indices.exists(index=INDEX_NAME)
        if not exists:
            await os_client.indices.create(index=INDEX_NAME, body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "salary_from": {"type": "float"},
                        "salary_to": {"type": "float"},
                        "city": {"type": "keyword"},
                        "vacancy_id": {"type": "long"},
                        "location": {"type": "geo_point"}, 
                        "attributes": {
                            "type": "object",
                            "dynamic": True
                        }
                    }
                }
            })
            logger.info(f"OpenSearch index '{INDEX_NAME}' created")
    except Exception as e:
        logger.error(f"Failed to setup index: {e}")

@broker.subscriber("vacancies_events")
async def handle_vacancy_event(msg: VacancyEvent):
    logger.info(f"Processing event: {msg.event} for vacancy_id: {msg.data.vacancy_id}")

    try:
        if msg.event in ("created", "updated"):
            await os_client.index(
                index=INDEX_NAME,
                id=msg.data.vacancy_id,
                body=msg.data.model_dump(),
                refresh=True
            )
            logger.info(f"Indexed/Updated vacancy {msg.data.vacancy_id}")

        elif msg.event == "deleted":
            try:
                await os_client.delete(index=INDEX_NAME, id=msg.data.vacancy_id)
                logger.info(f"Deleted vacancy {msg.data.vacancy_id}")
            except os_exceptions.NotFoundError:
                logger.warning(f"Vacancy {msg.data.vacancy_id} not found for deletion")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise e