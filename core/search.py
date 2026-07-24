from decouple import config
from opensearchpy import AsyncOpenSearch

OPENSEARCH_URL = config("OPENSEARCH_URL", default="http://localhost:9200")

client = AsyncOpenSearch(
    hosts=[OPENSEARCH_URL],
    use_ssl=False,
    verify_certs=False
)

async def search_vacancies(
    query: str = None, 
    lat: float = None, 
    lon: float = None,
    radius_km: int = 10,
    limit: int = 20, 
    offset: int = 0,
):
    """
    Searches for vacancies in OpenSearch.
    Returns a list of IDs of found vacancies.
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
    
    if query:
        sort_params.append("_score")

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
    
    sort_params.append({"vacancy_id": "desc"})

    try:
        response = await client.search(
            index="vacancies",
            body={
                "query": search_query,
                "from": offset,
                "size": limit,
                "sort": sort_params  
            },
            _source=["vacancy_id"]
        )

        hits = response["hits"]["hits"]
        vacancy_ids = [hit["_source"]["vacancy_id"] for hit in hits]
        return vacancy_ids

    except Exception as e:
        print(f"OpenSearch error: {e}")
        return []