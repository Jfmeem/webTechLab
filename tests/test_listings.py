from decimal import Decimal

from sqlalchemy.orm import Session


LISTING = {
    "title": "Python tutoring",
    "description": "One beginner lesson",
    "price": "500.25",
    "delivery_days": 2,
}


def register_and_login(client, username, role="provider"):
    credentials = {"username": username, "password": "test-password"}
    registration = client.post("/users", json={**credentials, "role": role})
    assert registration.status_code == 201
    account = registration.json()
    assert set(account) == {"id", "username", "role"}

    login = client.post("/login", data=credentials)
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    return account["id"], {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_listing_crud_lifecycle(client, db_engine):
    from models import ServiceListing

    provider_id, headers = register_and_login(client, "owner")

    response = client.get("/listings")
    assert response.status_code == 200
    assert response.json() == []

    response = client.post("/listings", json=LISTING, headers=headers)
    assert response.status_code == 201
    listing_id = response.json()["id"]
    detail_url = f"/listings/{listing_id}"

    with Session(bind=db_engine) as db:
        listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).one()
        assert listing.provider_id == provider_id
        assert listing.price == Decimal("500.25")

    response = client.get("/listings")
    assert response.status_code == 200
    assert [listing["id"] for listing in response.json()] == [listing_id]

    response = client.get(detail_url)
    assert response.status_code == 200
    assert response.json()["title"] == LISTING["title"]
    assert response.json()["provider_id"] == provider_id

    response = client.patch(detail_url, json={"title": "Advanced Python"}, headers=headers)
    assert response.status_code == 200
    with Session(bind=db_engine) as db:
        listing = db.query(ServiceListing).filter(ServiceListing.id == listing_id).one()
        assert listing.title == "Advanced Python"
        assert listing.description == LISTING["description"]
        assert listing.delivery_days == LISTING["delivery_days"]

    response = client.delete(detail_url, headers=headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(detail_url).status_code == 404
    with Session(bind=db_engine) as db:
        assert db.query(ServiceListing).count() == 0


def test_invalid_listing_and_missing_id(client):
    _, headers = register_and_login(client, "owner")

    response = client.post("/listings", json={**LISTING, "delivery_days": 0}, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "delivery_days"]
    assert client.get("/listings").json() == []

    missing_url = "/listings/999"
    assert client.get(missing_url).status_code == 404
    assert client.patch(missing_url, json={"title": "Updated"}, headers=headers).status_code == 404
    assert client.delete(missing_url, headers=headers).status_code == 404


def test_listing_permissions(client):
    _, owner_headers = register_and_login(client, "owner")
    _, other_headers = register_and_login(client, "other_provider")
    _, customer_headers = register_and_login(client, "customer", role="customer")

    assert client.post("/listings", json=LISTING).status_code == 401
    assert client.post("/listings", json=LISTING, headers=customer_headers).status_code == 403

    created = client.post("/listings", json=LISTING, headers=owner_headers)
    assert created.status_code == 201
    detail_url = f"/listings/{created.json()['id']}"

    response = client.patch(detail_url, json={"title": "Changed"}, headers=other_headers)
    assert response.status_code == 403
    assert client.delete(detail_url, headers=other_headers).status_code == 403
    response = client.get(detail_url)
    assert response.status_code == 200
    assert response.json()["title"] == LISTING["title"]
