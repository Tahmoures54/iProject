# tests/test_users.py
def test_users_requires_login(client):
    response = client.get("/users/")
    if response.status_code == 404:
        response = client.get("/users")
    assert response.status_code in (302, 401)