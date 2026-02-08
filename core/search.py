from decouple import config
from opensearchpy import AsyncOpenSearch

OPENSEARCH_URL = config("OPENSEARCH_URL")


client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)

async def search_ads(query: str = None, limit: int = 20, offset: int = 0):
    """
    Searches for ads in OpenSearch.
    Returns a list of IDs of found ads.
    """

    search_query = {"match_all": {}}

    if query:
        search_query = {
            "multi_match": {
                "query": query,
                "fields": ["title^3", "description"],
                "fuzziness": "AUTO"
            }
        }

    try:
        response = await client.search(
            index="ads",
            body={
                "query": search_query,
                "from": offset,
                "size": limit,
                "sort": ["_score", {"ad_id": "desc"}] if query else [{"ad_id": "desc"}]
            },
            _source=["ad_id"]
        )

        hits = response["hits"]["hits"]
        ad_ids = [hit["_source"]["ad_id"] for hit in hits]
        return ad_ids

    except Exception as e:
        print(f"OpenSearch error: {e}")
        return []
