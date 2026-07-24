import pytest
from django.test import Client
from ninja_jwt.tokens import RefreshToken

from ads.models import Category, Company
from core.models import OutboxEvent


@pytest.fixture
def auth_client(django_user_model):
    """Фикстура для создания клиента с JWT токеном"""
    user = django_user_model.objects.create_user(username="test_hr", password="pwd")
    refresh = RefreshToken.for_user(user)
    
    client = Client()
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {refresh.access_token}"
    return client, user


@pytest.mark.django_db
def test_create_vacancy_generates_outbox_event(auth_client):
    client, user = auth_client
    
    category = Category.add_root(name="Development", slug="dev")
    Company.objects.create(name="TechCorp", owner=user)

    payload = {
        "category_id": category.id,
        "title": "Senior Python Developer",
        "description": "FastAPI, Django, Kafka",
        "salary_from": 300000,
        "currency": "RUB",
        "city": "Batumi",
        "attributes": {"grade": "Senior", "format": "Remote"},
        "lat": 41.6168,
        "lon": 41.6367
    }

    response = client.post(
        "/api/jobs/vacancies", 
        data=payload, 
        content_type="application/json"
    )
    
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["title"] == payload["title"]

    outbox_events = OutboxEvent.objects.filter(processed=False)
    assert outbox_events.count() == 1
    
    event = outbox_events.first()
    assert event.topic == "vacancies_events"
    assert event.payload["event"] == "created"
    assert event.payload["data"]["vacancy_id"] == data["id"]
    assert event.payload["data"]["city"] == "Batumi"
    
from unittest.mock import patch
from model_bakery import baker
from ads.models import Vacancy

@pytest.mark.django_db
@patch("ads.api.search_vacancies")
def test_list_vacancies(mock_search_vacancies, auth_client):
    client, _ = auth_client
    
    vacancies = baker.make(Vacancy, _quantity=3)
    
    mock_search_vacancies.return_value = [v.id for v in vacancies]
    
    response = client.get("/api/jobs/vacancies?q=developer&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    mock_search_vacancies.assert_called_once_with(
        query="developer",
        lat=None,
        lon=None,
        radius_km=10,
        limit=10,
        offset=0
    )


@pytest.mark.django_db
def test_get_vacancy(auth_client):
    client, user = auth_client
    vacancy = baker.make(Vacancy)
    
    response = client.get(f"/api/jobs/vacancies/{vacancy.id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == vacancy.id
    assert response.json()["title"] == vacancy.title

@pytest.mark.django_db
def test_list_categories(auth_client):
    client, _ = auth_client
    
    root = Category.add_root(name="IT", slug="it")
    root.add_child(name="Backend", slug="backend")
    
    response = client.get("/api/jobs/categories")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "IT"
    assert len(data[0]["children"]) == 1
    assert data[0]["children"][0]["name"] == "Backend"

@pytest.mark.django_db
def test_get_category_breadcrumbs(auth_client):
    client, _ = auth_client
    
    root = Category.add_root(name="IT", slug="it")
    child = root.add_child(name="Backend", slug="backend")
    
    response = client.get(f"/api/jobs/categories/{child.id}/breadcrumbs")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == root.id
    assert data[1]["id"] == child.id