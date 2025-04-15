# modules/ip_analyzer.py - Module d'analyse d'adresses IP

from flask import Blueprint, request, jsonify, current_app
import requests
import json
import socket
from database import log_activity
import ipaddress

ip_blueprint = Blueprint('ip_analyzer', __name__)

@ip_blueprint.route('/analyze', methods=['POST'])
def analyze_ip():
    """Analyse une adresse IP et renvoie des informations géographiques et de réseau"""
    ip_address = request.json.get('ip')
    
    # Validation basique
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return jsonify({'error': 'Adresse IP invalide'}), 400
    
    # Log de l'activité
    log_activity('ip_analyzer', 'analyze', ip_address)
    
    # Vérifier si l'adresse est privée
    try:
        is_private = ipaddress.ip_address(ip_address).is_private
        if is_private:
            return jsonify({
                'ip': ip_address,
                'is_private': True,
                'info': 'Cette adresse IP est dans une plage privée'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Utiliser ipinfo.io pour obtenir des données géographiques
    api_key = current_app.config.get('IPINFO_API_KEY', '')
    url = f"https://ipinfo.io/{ip_address}/json"
    
    if api_key:
        url += f"?token={api_key}"
        
    try:
        response = requests.get(url)
        data = response.json()
        
        # Ajouter des informations supplémentaires avec socket si possible
        try:
            hostname = socket.gethostbyaddr(ip_address)[0]
            data['hostname'] = hostname
        except socket.herror:
            data['hostname'] = 'Non disponible'
            
        # Logs
        log_activity('ip_analyzer', 'analyze_result', ip_address, json.dumps(data))
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'analyse de l\'IP: {str(e)}'}), 500

@ip_blueprint.route('/whois', methods=['POST'])
def get_whois():
    """Obtient des informations WHOIS pour une adresse IP"""
    ip_address = request.json.get('ip')
    
    # À implémenter avec une bibliothèque Python pour WHOIS
    # Exemple minimal avec un service tiers
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        data = response.json()
        
        log_activity('ip_analyzer', 'whois', ip_address, json.dumps(data))
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des données WHOIS: {str(e)}'}), 500