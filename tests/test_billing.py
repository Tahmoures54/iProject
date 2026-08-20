def test_pricing_page(client):
    response = client.get("/billing/pricing")
    assert response.status_code == 200
