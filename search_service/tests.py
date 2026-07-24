import pytest
from unittest.mock import AsyncMock, patch

from faststream.kafka import TestKafkaBroker
from search_service.main import broker, app

@pytest.mark.asyncio
@patch("search_service.main.os_client")
async def test_vacancy_event_handler_indexes_document(mock_os_client):
    mock_os_client.index = AsyncMock()
    
    event_payload = {
        "event": "created",
        "data": {
            "vacancy_id": 42,
            "title": "Data Engineer",
            "description": "ClickHouse, Airflow",
            "salary_from": 4000.0,
            "city": "Remote",
            "attributes": {"skills": ["Python", "SQL"]},
            "location": {"lat": 41.6, "lon": 41.6}
        }
    }

    async with TestKafkaBroker(broker) as br:
        await br.publish(event_payload, topic="vacancies_events")
        
        mock_os_client.index.assert_called_once()
        
        call_kwargs = mock_os_client.index.call_args.kwargs
        assert call_kwargs["index"] == "vacancies"
        assert call_kwargs["id"] == 42
        assert call_kwargs["body"]["title"] == "Data Engineer"


@pytest.mark.asyncio
@patch("search_service.main.os_client")
async def test_vacancy_event_handler_deletes_document(mock_os_client):
    mock_os_client.delete = AsyncMock()
    
    event_payload = {
        "event": "deleted",
        "data": {
            "vacancy_id": 42,
            "title": "Data Engineer",
            "description": "...",
            "city": "Remote"
        }
    }

    async with TestKafkaBroker(broker) as br:
        await br.publish(event_payload, topic="vacancies_events")
        
        mock_os_client.delete.assert_called_once_with(
            index="vacancies", 
            id=42
        )