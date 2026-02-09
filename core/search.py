from decouple import config
from opensearchpy import AsyncOpenSearch

OPENSEARCH_URL = config("OPENSEARCH_URL")


client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)

async def search_ads(
    query: str = None, 
    lat: float = None, 
    lon: float = None,
    radius_km: int = 10,
    limit: int = 20, 
    offset: int = 0,
):
    """
    Searches for ads in OpenSearch.
    Returns a list of IDs of found ads.
    """

    search_query = {
        "bool": {
            "must": [],
            "filter": []
        }
    }

    if query:
        search_query["bool"]["must"].append({
            "multi_match": {
                "query": query,
                "fields": ["title^3", "description"],
                "fuzziness": "AUTO"
            }
        })
    else:
        if not lat: 
            search_query = {"match_all": {}}
    
    if lat is not None and lon is not None:
        search_query = {
            "bool": {
                "must": search_query.get("bool", {}).get("must", []),
                "filter": []
            }
        }
        
        search_query["bool"]["filter"].append({
            "geo_distance": {
                "distance": f"{radius_km}km",
                "location": {
                    "lat": lat,
                    "lon": lon
                }
            }
        })  

    sort_params = []
    if lat and lon:
        sort_params.append({
            "_geo_distance": {
                "location": {"lat": lat, "lon": lon},
                "order": "asc",
                "unit": "km",
                "mode": "min",
                "distance_type": "arc"
            }
        })
    
    sort_params.append({"ad_id": "desc"})

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
