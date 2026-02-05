from faststream import FastStream
from faststream.kafka import KafkaBroker
from opensearchpy import AsyncOpenSearch


BROKER_URL = "redpanda:9092"
OPENSEARCH_URL = "http://opensearch:9200"


broker = KafkaBroker(BROKER_URL)
app = FastStream(broker)


os_client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)


@app.on_startup
async def setup_index():
    exists = await os_client.indices.exists(index="ads")
    if not exists:
        await os_client.indices.create(index="ads", body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "price": {"type": "float"},
                    "city": {"type": "keyword"}
                }
            }
        })
        print("OpenSearch index 'ads' created")


@broker.subscriber("ads_events")
async def handle_ad_event(msg: dict):
    event_type = msg.get("event")
    
    if event_type == "created":
        print(f"Received new ad: {msg['title']}")
        
        await os_client.index(
            index="ads",
            id=msg["ad_id"],
            body={
                "title": msg["title"],
                "description": msg["description"],
                "price": float(msg["price"]),
                "city": msg["city"]
            }
        )
        print(f"Indexed ad {msg['ad_id']} to OpenSearch")