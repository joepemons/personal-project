from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime
import threading
import time 
import pytz

app = Flask(__name__)

BASE_URL = "https://homeassistant.emonshomelab.com/api"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3M2QwODc1MTZhZWQ0NGNjOWI4ZWJmMTdlZDYxNWRhOCIsImlhdCI6MTczMzQzMDIzMCwiZXhwIjoyMDQ4NzkwMjMwfQ.ttxKn0nOeXXMwHQtmHbP8usxQnso5kVMbVYS06PcZ7Y"

WEBHOOKS = {
    'ssh': '-8HrzwKLOwTuaOIRGM4jSknMs',
    'dhcp': '-VQaPgH5cdMHyfSOZkE9hwxgY',
    'dns': '-CBXI6CkyFBOSxMabOUA3FyNM',
    'router_reboot': '-lV8hUlfcHhSDXRxtsD_Txz1R',
    'ap_reboot': '-5WtZjFHi26UfwYdIzYukIylY'
}

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

network_history = []
MAX_HISTORY = 50

def format_timestamp(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        amsterdam_time = dt.astimezone(amsterdam_tz)
        return amsterdam_time.strftime('%H:%M:%S')
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        return timestamp_str

def get_sensor_data(sensor_id):
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
    global network_history
    while True:
        sensor_data = get_sensor_data(SENSORS['network_speed'])
        if sensor_data and sensor_data.get('state'):
            try:
                value = float(sensor_data['state'])
                current_time = datetime.now(pytz.timezone('Europe/Amsterdam')).strftime('%H:%M:%S')
                network_history.append({
                    'value': value,
                    'timestamp': current_time
                })
                if len(network_history) > MAX_HISTORY:
                    network_history = network_history[-MAX_HISTORY:]
            except (ValueError, TypeError):
                pass
        time.sleep(5)

background_thread = threading.Thread(target=update_network_history, daemon=True)
background_thread.start()

@app.route('/api/network-history')
def get_network_history():
    return jsonify(network_history)

@app.route('/api/toggle/<service>', methods=['POST'])
def toggle_service(service):
    if service not in WEBHOOKS:
        return jsonify({'success': False, 'message': 'Invalid service'})
    
    webhook_id = WEBHOOKS[service]
    url = f"https://homeassistant.emonshomelab.com/api/webhook/{webhook_id}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            verify=True
        )
        
        service_name = 'Access Point' if service == 'ap_reboot' else 'Router' if service == 'router_reboot' else service.upper()
        action = 'rebooted' if 'reboot' in service else 'toggled'
        
        if response.status_code == 200:
            return jsonify({
                'success': True, 
                'message': f'{service_name} {action} successfully'
            })
        else:
            print(f"Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return jsonify({
                'success': False, 
                'message': f'Failed to {action} {service_name}: Status code {response.status_code}'
            })
            
    except requests.RequestException as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error with {service_name}: {str(e)}'
        })

@app.route('/get_current_metrics')
def get_current_metrics():
    system_data = {}
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
    return jsonify(system_data)

@app.route('/')
def index():
    system_data = {}
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