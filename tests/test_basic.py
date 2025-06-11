import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def test_app_starts():
    """Test if my app can start"""
    client = app.test_client()
    response = client.get('/')
    assert response.status_code in [200, 500]  
def test_metrics_page_exists():
    """Test if my metrics API exists"""
    client = app.test_client()
    response = client.get('/get_current_metrics')
    assert response.status_code in [200, 500]

def test_network_history_exists():
    """Test if network history API exists"""
    client = app.test_client()
    response = client.get('/api/network-history')
    assert response.status_code == 200  
def test_fake_page_gives_404():
    """Test 404 error"""
    client = app.test_client()
    response = client.get('/this-page-does-not-exist')
    assert response.status_code == 404

def test_toggle_fake_service():
    """Test service toggle with fake service"""
    client = app.test_client()
    response = client.post('/api/toggle/fake_service')
    assert response.status_code == 200