import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock

from src.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def mock_crud():
    with patch("src.api.routes.crud") as mock:
        yield mock

@pytest.fixture
def mock_engine():
    with patch("src.api.routes.nav_estimator") as me, \
         patch("src.api.routes.error_correction") as ec:
        yield me, ec

@pytest.fixture
def mock_data():
    with patch("src.api.routes.fund_list") as fl, \
         patch("src.api.routes.holdings") as ho:
        yield fl, ho

def test_get_watchlist(mock_crud):
    mock_crud.get_watchlist.return_value = [{"fund_code": "000001", "fund_name": "Test"}]
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    assert response.json() == [{"fund_code": "000001", "fund_name": "Test", "added_at": None}]

def test_add_to_watchlist_existing(mock_crud):
    mock_crud.get_fund.return_value = {"fund_code": "000001", "fund_name": "Test"}
    mock_crud.add_to_watchlist.return_value = True
    
    response = client.post("/api/watchlist", json={"fund_code": "000001"})
    assert response.status_code == 200
    assert response.json() is True
    mock_crud.add_to_watchlist.assert_called_with("000001", "Test")

def test_add_to_watchlist_new(mock_crud, mock_data):
    fl, ho = mock_data
    mock_crud.get_fund.side_effect = [None, {"fund_code": "000002", "fund_name": "New"}]
    fl.save_fund_info.return_value = True
    mock_crud.add_to_watchlist.return_value = True
    
    response = client.post("/api/watchlist", json={"fund_code": "000002"})
    assert response.status_code == 200
    fl.save_fund_info.assert_called_once()
    ho.save_fund_holdings.assert_called_once()

def test_remove_from_watchlist(mock_crud):
    mock_crud.remove_from_watchlist.return_value = True
    response = client.delete("/api/watchlist/000001")
    assert response.status_code == 200
    
    mock_crud.remove_from_watchlist.return_value = False
    response = client.delete("/api/watchlist/999999")
    assert response.status_code == 404

def test_get_fund_info(mock_crud):
    mock_crud.get_fund.return_value = {"fund_code": "000001", "fund_name": "Test", "latest_nav": 1.0}
    response = client.get("/api/funds/000001")
    assert response.status_code == 200
    assert response.json()["fund_code"] == "000001"

def test_get_estimate(mock_engine):
    me, ec = mock_engine
    me.estimate_fund_nav.return_value = {
        "fund_code": "000001", "estimated_nav": 1.1, "estimated_return": 1.0
    }
    ec.correct_fund_estimate.return_value = {
        "corrected_nav": 1.09, "corrected_return": 0.9, "is_corrected": True
    }
    
    response = client.get("/api/funds/000001/estimate")
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_nav"] == 1.1
    assert data["corrected_nav"] == 1.09
    assert data["is_corrected"] is True
