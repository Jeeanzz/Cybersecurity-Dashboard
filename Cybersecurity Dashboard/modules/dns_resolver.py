# modules/dns_resolver.py - Module de résolution DNS

from flask import Blueprint, request, jsonify
import socket
import dns.resolver
from database import log_activity

dns_blueprint = Blueprint('dns_resolver', __name__)

@dns_blueprint.route('/resolve', methods=['POST'])
def resolve_domain():
    """Résout un nom de domaine en adresse IP"""
    domain = request.json.get('domain')
    
    if not domain:
        return jsonify({'error': 'Domaine non spécifié'}), 400
    
    try:
        # Résolution simple avec socket
        ip_address = socket.gethostbyname(domain)
        
        # Log de l'activité
        log_activity('dns_resolver', 'resolve', domain, ip_address)
        
        return jsonify({
            'domain': domain,
            'ip': ip_address
        })
    except socket.gaierror:
        return jsonify({'error': 'Impossible de résoudre le domaine'}), 404
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la résolution DNS: {str(e)}'}), 500

@dns_blueprint.route('/lookup', methods=['POST'])
def dns_lookup():
    """Effectue une recherche DNS complète (A, MX, NS, etc.)"""
    domain = request.json.get('domain')
    record_type = request.json.get('type', 'A')  # Type par défaut: A
    
    if not domain:
        return jsonify({'error': 'Domaine non spécifié'}), 400
    
    valid_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']
    if record_type not in valid_types:
        return jsonify({'error': f'Type de record invalide. Valeurs acceptées: {", ".join(valid_types)}'}), 400
    
    try:
        # Utilisation de dnspython pour des requêtes DNS plus complètes
        resolver = dns.resolver.Resolver()
        answers = resolver.resolve(domain, record_type)
        
        results = []
        for rdata in answers:
            if record_type == 'MX':
                results.append({'preference': rdata.preference, 'exchange': rdata.exchange.to_text()})
            elif record_type == 'SOA':
                results.append({
                    'mname': rdata.mname.to_text(),
                    'rname': rdata.rname.to_text(),
                    'serial': rdata.serial,
                    'refresh': rdata.refresh,
                    'retry': rdata.retry,
                    'expire': rdata.expire,
                    'minimum': rdata.minimum
                })
            else:
                results.append(rdata.to_text())
        
        # Log de l'activité
        log_activity('dns_resolver', 'lookup', f"{domain} ({record_type})", str(results))
        
        return jsonify({
            'domain': domain,
            'type': record_type,
            'results': results
        })
    except dns.resolver.NXDOMAIN:
        return jsonify({'error': 'Domaine inexistant'}), 404
    except dns.resolver.NoAnswer:
        return jsonify({'error': f'Aucun enregistrement de type {record_type} trouvé'}), 404
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la requête DNS: {str(e)}'}), 500

@dns_blueprint.route('/reverse', methods=['POST'])
def reverse_dns():
    """Effectue une résolution DNS inverse (IP vers nom d'hôte)"""
    ip = request.json.get('ip')
    
    if not ip:
        return jsonify({'error': 'Adresse IP non spécifiée'}), 400
    
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        
        # Log de l'activité
        log_activity('dns_resolver', 'reverse', ip, hostname)
        
        return jsonify({
            'ip': ip,
            'hostname': hostname
        })
    except socket.herror:
        return jsonify({'error': 'Impossible de résoudre l\'adresse IP en nom d\'hôte'}), 404
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la résolution DNS inverse: {str(e)}'}), 500