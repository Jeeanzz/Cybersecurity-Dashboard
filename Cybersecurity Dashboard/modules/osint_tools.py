# modules/osint_tools.py - Module d'outils OSINT

from flask import Blueprint, request, jsonify, current_app
import requests
import json
import re
from database import log_activity

osint_blueprint = Blueprint('osint_tools', __name__)

@osint_blueprint.route('/email-info', methods=['POST'])
def email_osint():
    """Recherche d'informations sur une adresse email"""
    email = request.json.get('email')
    
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': 'Adresse email invalide'}), 400
    
    # Log de l'activité
    log_activity('osint', 'email_search', email)
    
    # Structure pour les résultats
    results = {
        'email': email,
        'haveibeenpwned': None,
        'github': None,
        'gravatar': None
    }
    
    # Vérification avec HaveIBeenPwned
    hibp_api_key = current_app.config.get('HIBP_API_KEY', '')
    if hibp_api_key:
        try:
            headers = {
                'hibp-api-key': hibp_api_key,
                'User-Agent': 'CyberSec-Platform'
            }
            response = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers=headers
            )
            
            if response.status_code == 200:
                results['haveibeenpwned'] = {
                    'breached': True,
                    'breaches': response.json()
                }
            elif response.status_code == 404:
                results['haveibeenpwned'] = {
                    'breached': False,
                    'message': 'Aucune fuite de données trouvée'
                }
            else:
                results['haveibeenpwned'] = {
                    'error': f'Erreur lors de la requête (code {response.status_code})'
                }
        except Exception as e:
            results['haveibeenpwned'] = {'error': str(e)}
    
# Recherche sur GitHub (API publique)
    try:
        response = requests.get(
            f"https://api.github.com/search/users?q={email}",
            headers={'User-Agent': 'CyberSec-Platform'}
        )
        
        if response.status_code == 200:
            data = response.json()
            results['github'] = {
                'total_count': data.get('total_count', 0),
                'users': [{'login': user['login'], 'url': user['html_url']} for user in data.get('items', [])]
            }
        else:
            results['github'] = {
                'error': f'Erreur lors de la requête (code {response.status_code})'
            }
    except Exception as e:
        results['github'] = {'error': str(e)}
    
    # Recherche Gravatar
    import hashlib
    try:
        # Hachage de l'email pour Gravatar
        hashed_email = hashlib.md5(email.lower().encode()).hexdigest()
        gravatar_url = f"https://www.gravatar.com/{hashed_email}.json"
        
        response = requests.get(
            gravatar_url,
            headers={'User-Agent': 'CyberSec-Platform'}
        )
        
        if response.status_code == 200:
            results['gravatar'] = {
                'found': True,
                'data': response.json()
            }
        else:
            results['gravatar'] = {
                'found': False,
                'message': 'Profil Gravatar non trouvé'
            }
    except Exception as e:
        results['gravatar'] = {'error': str(e)}
    
    # Log des résultats
    log_activity('osint', 'email_search_result', email, json.dumps({
        'haveibeenpwned': results['haveibeenpwned'] is not None and 'error' not in results['haveibeenpwned'],
        'github': results['github'] is not None and 'error' not in results['github'],
        'gravatar': results['gravatar'] is not None and 'error' not in results['gravatar']
    }))
    
    return jsonify(results)

@osint_blueprint.route('/username-info', methods=['POST'])
def username_osint():
    """Recherche d'informations sur un nom d'utilisateur"""
    username = request.json.get('username')
    
    if not username or len(username) < 3:
        return jsonify({'error': 'Nom d\'utilisateur invalide (minimum 3 caractères)'}), 400
    
    # Log de l'activité
    log_activity('osint', 'username_search', username)
    
    # Structure pour les résultats
    results = {
        'username': username,
        'github': None,
        'twitter': None,
        'reddit': None
    }
    
    # Recherche sur GitHub
    try:
        response = requests.get(
            f"https://api.github.com/users/{username}",
            headers={'User-Agent': 'CyberSec-Platform'}
        )
        
        if response.status_code == 200:
            data = response.json()
            results['github'] = {
                'found': True,
                'name': data.get('name'),
                'company': data.get('company'),
                'blog': data.get('blog'),
                'location': data.get('location'),
                'email': data.get('email'),
                'bio': data.get('bio'),
                'public_repos': data.get('public_repos'),
                'followers': data.get('followers'),
                'created_at': data.get('created_at'),
                'url': data.get('html_url')
            }
        else:
            results['github'] = {
                'found': False,
                'message': 'Utilisateur GitHub non trouvé'
            }
    except Exception as e:
        results['github'] = {'error': str(e)}
    
    # Vérification simplifiée des autres plateformes (sans API officielle)
    # Note: Ces vérifications sont basiques et peuvent donner des faux positifs
    
    # Vérification Reddit
    try:
        response = requests.get(
            f"https://www.reddit.com/user/{username}/about.json",
            headers={'User-Agent': 'CyberSec-Platform'}
        )
        
        if response.status_code == 200:
            data = response.json()
            user_data = data.get('data', {})
            results['reddit'] = {
                'found': True,
                'name': user_data.get('name'),
                'created_utc': user_data.get('created_utc'),
                'karma': {
                    'post': user_data.get('link_karma'),
                    'comment': user_data.get('comment_karma')
                },
                'url': f"https://www.reddit.com/user/{username}"
            }
        else:
            results['reddit'] = {
                'found': False,
                'message': 'Utilisateur Reddit non trouvé'
            }
    except Exception as e:
        results['reddit'] = {'error': str(e)}
    
    # Log des résultats
    log_activity('osint', 'username_search_result', username, json.dumps({
        'github': results['github'] is not None and results['github'].get('found', False),
        'reddit': results['reddit'] is not None and results['reddit'].get('found', False),
    }))
    
    return jsonify(results)

@osint_blueprint.route('/shodan-search', methods=['POST'])
def shodan_search():
    """Recherche via l'API Shodan"""
    query = request.json.get('query')
    
    if not query:
        return jsonify({'error': 'Requête non spécifiée'}), 400
    
    # Log de l'activité
    log_activity('osint', 'shodan_search', query)
    
    shodan_api_key = current_app.config.get('SHODAN_API_KEY', '')
    if not shodan_api_key:
        return jsonify({'error': 'Clé API Shodan non configurée'}), 500
    
    try:
        # Recherche Shodan
        response = requests.get(
            f"https://api.shodan.io/shodan/host/search?key={shodan_api_key}&query={query}"
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Formatage des résultats
            formatted_results = {
                'query': query,
                'total': data.get('total', 0),
                'matches': []
            }
            
            # Extraction des informations pertinentes
            for match in data.get('matches', []):
                formatted_results['matches'].append({
                    'ip': match.get('ip_str'),
                    'hostname': match.get('hostnames', []),
                    'org': match.get('org'),
                    'country': match.get('location', {}).get('country_name'),
                    'city': match.get('location', {}).get('city'),
                    'port': match.get('port'),
                    'product': match.get('product'),
                    'version': match.get('version'),
                    'data': match.get('data')
                })
            
            # Log des résultats
            log_activity('osint', 'shodan_search_result', query, 
                         f"Résultats trouvés: {data.get('total', 0)}")
            
            return jsonify(formatted_results)
        else:
            return jsonify({
                'error': f'Erreur Shodan ({response.status_code}): {response.text}'
            }), response.status_code
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la recherche Shodan: {str(e)}'}), 500