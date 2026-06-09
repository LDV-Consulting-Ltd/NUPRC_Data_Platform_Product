"""Data products endpoint tests (v0.1 envelope)."""


def test_data_products_returns_envelope(tanna_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_gold_tables",
        lambda: ([], ["Gold unavailable"]),
    )
    response = tanna_client.get("/api/v1/tanna/data-products", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["object_type"] == "data_products"
    assert data["implementation_status"] == "implemented"
    assert isinstance(data["items"], list)


def test_data_products_primary_mapping(tanna_client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_gold_tables",
        lambda: ([
            {
                "physical_name": "gold_oil_fact_production",
                "display_name": "Oil — Production (Fact)",
                "description": "test",
                "row_count": 10,
                "last_updated": None,
            }
        ], []),
    )
    monkeypatch.setattr(
        "app.tanna_connector.adapters.catalog_adapter.get_table_display",
        lambda: ({}, []),
    )
    data = tanna_client.get("/api/v1/tanna/data-products", headers=auth_headers).json()
    ids = [p["id"] for p in data["items"]]
    assert "petrocore:data_product:gold_oil_fact_production" in ids
