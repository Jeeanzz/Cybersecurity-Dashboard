# modules/network_analyzer.py - Module d'analyse du réseau local

from flask import Blueprint, request, jsonify
import subprocess
import threading
import socket
import ipaddress
from scapy.all import ARP, Ether, srp
from database import log_activity

network_blueprint = Blueprint('network_analyzer', __name__)

@network_blueprint.route('/scan-local', methods=['POST'])
def scan_local_network():
    """Scanne le réseau local en utilisant Scapy pour ARP discovery"""
    subnet = request.json.get('subnet')  # Format attendu: '192.168.1.0/24'
    
    if not subnet:
        return jsonify({'error': 'Sous-réseau non spécifié'}), 400
    
    try:
        # Validation du format du sous-réseau
        ipaddress.ip_network(subnet)
    except ValueError:
        return jsonify({'error': 'Format de sous-réseau invalide. Utilisez le format CIDR (ex: 192.168.1.0/24)'}), 400
    
    try:
        # Création d'un paquet ARP pour scanner le réseau
        arp = ARP(pdst=subnet)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast MAC
        packet = ether/arp
        
        # Envoi des paquets et réception des réponses
        result = srp(packet, timeout=3, verbose=0)[0]
        
        # Extraction des résultats
        devices = []
        for sent, received in result:
            devices.append({
                'ip': received.psrc,
                'mac': received.hwsrc
            })
        
        # Log de l'activité
        log_activity('network_analyzer', 'scan_local', 
                     f"Subnet: {subnet}", 
                     f"Appareils trouvés: {len(devices)}")
        
        return jsonify({
            'subnet': subnet,
            'devices_found': len(devices),
            'devices': devices
        })
    except Exception as e:
        return jsonify({'error': f'Erreur lors du scan du réseau local: {str(e)}'}), 500

@network_blueprint.route('/ping-sweep', methods=['POST'])
def ping_sweep():
    """Effectue un ping sweep sur une plage d'adresses IP"""
    ip_range = request.json.get('ip_range')  # Format attendu: '192.168.1.1-192.168.1.254' ou '192.168.1.0/24'
    
    if not ip_range:
        return jsonify({'error': 'Plage d\'IP non spécifiée'}), 400
    
    # Conversion en liste d'adresses IP
    ip_list = []
    try:
        if '/' in ip_range:  # Format CIDR
            network = ipaddress.ip_network(ip_range, strict=False)
            ip_list = [str(ip) for ip in network.hosts()]
        elif '-' in ip_range:  # Format plage
            start_ip, end_ip = ip_range.split('-')
            start = ipaddress.IPv4Address(start_ip.strip())
            end = ipaddress.IPv4Address(end_ip.strip())
            ip_list = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]
        else:
            return jsonify({'error': 'Format de plage d\'IP invalide'}), 400
            
        # Limiter le nombre d'adresses IP pour éviter les abus
        if len(ip_list) > 255:
            return jsonify({'error': 'Plage d\'IP trop large. Limitez à 255 adresses maximum.'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Erreur lors du parsing de la plage d\'IP: {str(e)}'}), 400
    
    # Fonction pour ping une adresse IP
    def ping_ip(ip):
        try:
            # Option -c 1: envoyer 1 paquet, -W 1: timeout de 1 seconde
            if subprocess.call(['ping', '-c', '1', '-W', '1', ip], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL) == 0:
                return True
            return False
        except:
            return False
    
    # Ping en parallèle
    active_hosts = []
    threads = []
    results = {ip: False for ip in ip_list}
    
    def ping_worker(ip):
        results[ip] = ping_ip(ip)
    
    for ip in ip_list:
        thread = threading.Thread(target=ping_worker, args=(ip,))
        threads.append(thread)
        thread.start()
    
    # Attendre la fin de tous les pings
    for thread in threads:
        thread.join(timeout=5)
    
    # Recueillir les résultats
    active_hosts = [ip for ip in ip_list if results[ip]]
    
    # Log de l'activité
    log_activity('network_analyzer', 'ping_sweep', 
                 f"Plage: {ip_range} ({len(ip_list)} adresses)", 
                 f"Hôtes actifs trouvés: {len(active_hosts)}")
    
    # Tentative de résolution des noms d'hôtes pour les IP actives
    hosts_with_names = []
    for ip in active_hosts:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = "Unknown"
        hosts_with_names.append({
            'ip': ip,
            'hostname': hostname
        })
    
    return jsonify({
        'ip_range': ip_range,
        'total_ips': len(ip_list),
        'active_hosts': len(active_hosts),
        'hosts': hosts_with_names
    })