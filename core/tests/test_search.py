import pytest
from unittest.mock import AsyncMock, patch
from core.search import search_vacancies

@pytest.mark.asyncio
@patch("core.search.client")
async def test_search_vacancies_text_query(mock_client):
    mock_client.search = AsyncMock(return_value={
        "hits": {"hits": [{"_source": {"vacancy_id": 99}}]}
    })
    
    result = await search_vacancies(query="Python")
    
    assert result == [99]
    call_kwargs = mock_client.search.call_args.kwargs
    query_body = call_kwargs["body"]["query"]
    assert "multi_match" in str(query_body)

@pytest.mark.asyncio
@patch("core.search.client")
async def test_search_vacancies_geo_query(mock_client):
    mock_client.search = AsyncMock(return_value={"hits": {"hits": []}})
    
    await search_vacancies(lat=41.6, lon=41.6, radius_km=15)
    
    call_kwargs = mock_client.search.call_args.kwargs
    query_body = call_kwargs["body"]["query"]
    sort_body = call_kwargs["body"]["sort"]
    
    assert "geo_distance" in str(query_body)
    assert "_geo_distance" in sort_body[0]
    assert sort_body[0]["_geo_distance"]["distance_type"] == "arc"