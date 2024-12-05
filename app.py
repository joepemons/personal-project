from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Base API configuration
BASE_URL = "https://homeassistant.emonshomelab.com/api"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3M2QwODc1MTZhZWQ0NGNjOWI4ZWJmMTdlZDYxNWRhOCIsImlhdCI6MTczMzQzMDIzMCwiZXhwIjoyMDQ4NzkwMjMwfQ.ttxKn0nOeXXMwHQtmHbP8usxQnso5kVMbVYS06PcZ7Y"

# Webhook endpoints - exact webhook IDs from curl commands
WEBHOOKS = {
    'ssh': '-8HrzwKLOwTuaOIRGM4jSknMs',
    'dhcp': '-VQaPgH5cdMHyfSOZkE9hwxgY',
    'dns': '-CBXI6CkyFBOSxMabOUA3FyNM'
}

# List of sensors to monitor
SENSORS = {
    'network_speed': 'sensor.opnsense_interface_lan_inbytes_kilobytes_per_second',
    'memory_usage': 'sensor.opnsense_memory_used_percentage',
    'cpu_usage': 'sensor.opnsense_cpu_usage',
    'lan_status': 'sensor.opnsense_interface_lan_status',
    'wan_status': 'sensor.opnsense_interface_wan_status',
    'opt1_status': 'sensor.opnsense_interface_opt1_status',
    'opt2_status': 'sensor.opnsense_interface_opt2_status',
    'opt3_status': 'sensor.opnsense_interface_opt3_status',
    'opt4_status': 'sensor.opnsense_interface_opt4_status',
    'dhcp_leases': 'sensor.opnsense_dhcp_leases_all'
}

# Store historical network speed data (last 50 points)
network_history = []
MAX_HISTORY = 50

def format_timestamp(timestamp_str):
    """Format timestamp to a more readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except Exception:
        return timestamp_str

def get_sensor_data(sensor_id):
    """Fetch data for a specific sensor"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/states/{sensor_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {sensor_id}: {e}")
        return None

def update_network_history():
    """Update network speed history in the background"""
    global network_history
    while True:
        sensor_data = get_sensor_data(SENSORS['network_speed'])
        if sensor_data and sensor_data.get('state'):
            try:
                value = float(sensor_data['state'])
                current_time = datetime.now().strftime('%H:%M:%S')
                
                network_history.append({
                    'value': value,
                    'timestamp': current_time
                })
                
                # Keep only the last MAX_HISTORY points
                if len(network_history) > MAX_HISTORY:
                    network_history = network_history[-MAX_HISTORY:]
                    
            except (ValueError, TypeError):
                pass
        time.sleep(5)  # Update every 5 seconds

# Start the background data collection
background_thread = threading.Thread(target=update_network_history, daemon=True)
background_thread.start()

@app.route('/api/network-history')
def get_network_history():
    """API endpoint to get historical network data"""
    return jsonify(network_history)

@app.route('/api/toggle/<service>', methods=['POST'])
def toggle_service(service):
    """API endpoint to toggle services using exact curl command format"""
    if service not in WEBHOOKS:
        return jsonify({'success': False, 'message': 'Invalid service'})
    
    url = f"https://homeassistant.emonshomelab.com/api/webhook/{WEBHOOKS[service]}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    try:
        # Print the exact curl command being executed
        print(f'curl -X POST -H "Authorization: Bearer {API_TOKEN}" {url}')
        
        # Execute the request without content-type header to match curl exactly
        response = requests.post(
            url,
            headers=headers,
            verify=True
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True, 
                'message': f'{service.upper()} service toggled successfully'
            })
        else:
            print(f"Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({
                'success': False, 
                'message': f'Failed to toggle {service.upper()}: Status code {response.status_code}'
            })
            
    except requests.RequestException as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error toggling {service.upper()}: {str(e)}'
        })

@app.route('/')
def index():
    """Main route to display router data"""
    system_data = {}
    
    # Fetch current data for each sensor
    for key, sensor_id in SENSORS.items():
        sensor_data = get_sensor_data(sensor_id)
        if sensor_data:
            system_data[key] = {
                'state': sensor_data.get('state', 'N/A'),
                'last_updated': format_timestamp(sensor_data.get('last_updated', 'N/A')),
                'unit': sensor_data.get('attributes', {}).get('unit_of_measurement', ''),
                'friendly_name': sensor_data.get('attributes', {}).get('friendly_name', key.replace('_', ' ').title())
            }
        else:
            system_data[key] = {
                'state': 'Error',
                'last_updated': 'N/A',
                'unit': '',
                'friendly_name': key.replace('_', ' ').title()
            }
    
    return render_template('index.html', data=system_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)