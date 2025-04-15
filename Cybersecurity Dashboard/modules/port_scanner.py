# modules/port_scanner.py - Module de scan de ports

from flask import Blueprint, request, jsonify
import socket
import threading
import subprocess
import json
from database import log_activity
import ipaddress

port_blueprint = Blueprint('port_scanner', __name__)

def scan_port_socket(ip, port, timeout=1):
    """Scan un port unique en utilisant socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    result = sock.connect_ex((ip, port))
    is_open = result == 0
    sock.close()
    return is_open

@port_blueprint.route('/scan-socket', methods=['POST'])
def scan_with_socket():
    """Effectue un scan de ports en utilisant socket"""
    data = request.json
    ip = data.get('ip')
    ports = data.get('ports', [])  # Liste de ports à scanner
    
    # Validation de l'IP
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({'error': 'Adresse IP invalide'}), 400
    
    if not ports:
        # Si aucun port n'est spécifié, utiliser les ports courants
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 1433, 3306, 3389, 5900, 8080]
    
    # Limiter le nombre de ports à scanner pour éviter les abus
    if len(ports) > 1000:
        return jsonify({'error': 'Trop de ports demandés. Limitez à 1000 ports maximum.'}), 400
    
    results = {}
    threads = []
    
    # Utilisation de threads pour accélérer le scan
    def scan_worker(port):
        results[port] = scan_port_socket(ip, port)
    
    for port in ports:
        thread = threading.Thread(target=scan_worker, args=(port,))
        threads.append(thread)
        thread.start()
    
    # Attendre la fin de tous les scans
    for thread in threads:
        thread.join()
    
    # Formater les résultats
    open_ports = {port: service for port, service in results.items() if results[port]}
    
    # Log des résultats
    log_activity('port_scanner', 'socket_scan', 
                 f"IP: {ip}, Ports scannés: {len(ports)}", 
                 f"Ports ouverts trouvés: {len(open_ports)}")
    
    return jsonify({
        'ip': ip,
        'total_ports_scanned': len(ports),
        'open_ports': [port for port in ports if results[port]],
        'closed_ports': [port for port in ports if not results[port]]
    })

@port_blueprint.route('/scan-nmap', methods=['POST'])
def scan_with_nmap():
    """Effectue un scan de ports en utilisant nmap (nécessite nmap installé sur le serveur)"""
    data = request.json
    ip = data.get('ip')
    port_range = data.get('port_range', '1-1000')  # Format: "1-1000"
    
    # Validation de l'IP
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify({'error': 'Adresse IP invalide'}), 400
    
    # Limiter la plage de ports pour éviter les abus
    if '-' in port_range:
        start, end = map(int, port_range.split('-'))
        if end - start > 1000:
            return jsonify({'error': 'Plage de ports trop large. Limitez à 1000 ports maximum.'}), 400
    
    try:
        # Exécuter nmap avec paramètres de base
        # Note: Cela nécessite que nmap soit installé sur le serveur
        command = ['nmap', '-p', port_range, ip]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if stderr:
            return jsonify({'error': stderr.decode()}), 500
        
        # Analyse de la sortie nmap
        output = stdout.decode()
        
        # Extraction des ports ouverts (analyse simple)
        open_ports = []
        for line in output.splitlines():
            if 'open' in line and '/tcp' in line:
                parts = line.split()
                port = parts[0].split('/')[0]
                service = parts[-1] if len(parts) > 2 else "unknown"
                open_ports.append({'port': port, 'service': service})
        
        # Log des résultats
        log_activity('port_scanner', 'nmap_scan', 
                    f"IP: {ip}, Plage de ports: {port_range}", 
                    f"Ports ouverts trouvés: {len(open_ports)}")
        
        return jsonify({
            'ip': ip,
            'port_range': port_range,
            'open_ports': open_ports,
            'raw_output': output
        })
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'exécution de nmap: {str(e)}'}), 500