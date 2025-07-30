from flask import Flask, jsonify
import subprocess
import re

app = Flask(__name__)

@app.route('/admin/terminal-management/api/refresh-arp-table', methods=['GET'])
def refresh_arp_table():
    """API endpoint to refresh the ARP table and return the results."""
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            arp_entries = []
            for line in lines:
                # Match lines with IP and MAC addresses
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2}-[0-9a-f]{2})', line, re.IGNORECASE)
                if match:
                    arp_entries.append({
                        'ip_address': match.group(1),
                        'mac_address': match.group(2).upper(),
                        'hostname': 'Unknown',  # Placeholder for hostname
                        'device_type': 'Unknown',  # Placeholder for device type
                        'online': False  # Assume offline for ARP entries
                    })
            return jsonify({'arp_table': arp_entries}), 200
        else:
            return jsonify({'error': 'Failed to refresh ARP table: Non-zero return code'}), 500
    except Exception as e:
        return jsonify({'error': f'Error refreshing ARP table: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
