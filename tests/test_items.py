# tests/test_items.py
def test_items_requires_login(client):
    response = client.get("/items/")
    if response.status_code == 404:
        response = client.get("/items")
    assert response.status_code in (302, 401)