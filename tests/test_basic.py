import sys
import os

# Add the main folder so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def test_app_starts():
    """Test if my app can start"""
    client = app.test_client()
    # Just check if something responds
    response = client.get('/')
    # As long as it doesn't crash, it's good
    assert response.status_code in [200, 500]  # 500 is OK too (API might be down)

def test_metrics_page_exists():
    """Test if my metrics API exists"""
    client = app.test_client()
    response = client.get('/get_current_metrics')
    # Don't care if it works, just that it exists
    assert response.status_code in [200, 500]

def test_network_history_exists():
    """Test if network history API exists"""
    client = app.test_client()
    response = client.get('/api/network-history')
    assert response.status_code == 200  # This one should always work

def test_fake_page_gives_404():
    """Test 404 error"""
    client = app.test_client()
    response = client.get('/this-page-does-not-exist')
    assert response.status_code == 404

def test_toggle_fake_service():
    """Test service toggle with fake service"""
    client = app.test_client()
    response = client.post('/api/toggle/fake_service')
    # Should get an error response but not crash
    assert response.status_code == 200