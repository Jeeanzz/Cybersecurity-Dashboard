# modules/reverse_ip.py - Module de reverse IP en mode privé

from flask import Blueprint, request, jsonify, current_app
import requests
from database import log_activity

reverse_ip_blueprint = Blueprint('reverse_ip', __name__)

@reverse_ip_blueprint.route('/lookup', methods=['POST'])
def reverse_ip_lookup():
    """Recherche les domaines hébergés sur une adresse IP"""
    ip = request.json.get('ip')
    
    if not ip:
        return jsonify({'error': 'Adresse IP non spécifiée'}), 400
    
    # Log de l'activité
    log_activity('reverse_ip', 'lookup', ip)
    
    # Utiliser le service HackerTarget pour le reverse IP
    try:
        response = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={ip}")
        
        if response.status_code == 200:
            # Le service renvoie une liste de domaines séparés par des sauts de ligne
            domains = response.text.strip().split('\n')
            
            # Filtrer les erreurs potentielles
            if len(domains) == 1 and ('error' in domains[0].lower() or 'invalid' in domains[0].lower()):
                return jsonify({'error': domains[0]}), 400
                
            # Log des résultats
            log_activity('reverse_ip', 'lookup_result', ip, f"{len(domains)} domaines trouvés")
            
            return jsonify({
                'ip': ip,
                'domains_count': len(domains),
                'domains': domains
            })
        else:
            return jsonify({'error': f'Erreur de service: {response.text}'}), response.status_code
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la recherche reverse IP: {str(e)}'}), 500

@reverse_ip_blueprint.route('/whois-domain', methods=['POST'])
def domain_whois():
    """Obtient des informations WHOIS pour un domaine"""
    domain = request.json.get('domain')
    
    if not domain:
        return jsonify({'error': 'Domaine non spécifié'}), 400
    
    # Log de l'activité
    log_activity('reverse_ip', 'whois_domain', domain)
    
    # Utiliser le service HackerTarget pour le WHOIS
    try:
        response = requests.get(f"https://api.hackertarget.com/whois/?q={domain}")
        
        if response.status_code == 200:
            whois_data = response.text
            
            # Convertir en format plus structuré
            structured_data = {}
            for line in whois_data.split('\n'):
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    structured_data[key.strip()] = value.strip()
            
            # Log des résultats
            log_activity('reverse_ip', 'whois_domain_result', domain, "Succès")
            
            return jsonify({
                'domain': domain,
                'raw_whois': whois_data,
                'structured_data': structured_data
            })
        else:
            return jsonify({'error': f'Erreur de service: {response.text}'}), response.status_code
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la recherche WHOIS: {str(e)}'}), 500