# modules/virtual_number.py - Module de gestion des numéros virtuels

from flask import Blueprint, request, jsonify, current_app
import random
import string
from datetime import datetime
import threading
import time
from database import get_db_connection, log_activity

virtual_number_blueprint = Blueprint('virtual_number', __name__)

# Simulations des SMS reçus pour les numéros virtuels
virtual_sms_queue = {}
sms_simulation_running = False

def simulate_incoming_sms():
    """Simule l'arrivée de SMS pour les numéros virtuels"""
    global sms_simulation_running
    
    sms_simulation_running = True
    
    while sms_simulation_running:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupérer tous les numéros virtuels actifs
        cursor.execute('SELECT id, phone_number FROM virtual_numbers')
        numbers = cursor.fetchall()
        
        for number in numbers:
            # Simuler aléatoirement l'arrivée d'un SMS (10% de chance)
            if random.random() < 0.1:
                # Types de SMS simulés
                sms_types = [
                    {'sender': 'Facebook', 'message': f'Your Facebook verification code is: {random.randint(100000, 999999)}', 'is_otp': True},
                    {'sender': 'Google', 'message': f'Your Google verification code is: {random.randint(100000, 999999)}', 'is_otp': True},
                    {'sender': 'Twitter', 'message': f'Your Twitter verification code is: {random.randint(100000, 999999)}', 'is_otp': True},
                    {'sender': 'Amazon', 'message': f'Your Amazon OTP: {random.randint(100000, 999999)}', 'is_otp': True},
                    {'sender': 'Bank', 'message': f'Your transaction code: {random.randint(100000, 999999)}', 'is_otp': True},
                    {'sender': '+15551234567', 'message': 'Hello! How are you?', 'is_otp': False},
                    {'sender': 'Marketing', 'message': 'Check out our new offers!', 'is_otp': False}
                ]
                
                # Sélectionner aléatoirement un type de SMS
                sms = random.choice(sms_types)
                
                # Extraire le code OTP si c'est un SMS d'OTP
                otp_code = None
                if sms['is_otp']:
                    import re
                    match = re.search(r'\d{6}', sms['message'])
                    if match:
                        otp_code = match.group(0)
                
                # Ajouter le SMS à la base de données
                cursor.execute(
                    'INSERT INTO received_sms (virtual_number_id, sender, message, is_otp, otp_code) VALUES (?, ?, ?, ?, ?)',
                    (number['id'], sms['sender'], sms['message'], 1 if sms['is_otp'] else 0, otp_code)
                )
                
                # Mettre à jour la date de dernière utilisation du numéro
                cursor.execute(
                    'UPDATE virtual_numbers SET last_used = CURRENT_TIMESTAMP WHERE id = ?',
                    (number['id'],)
                )
                
                conn.commit()
                
                # Ajouter à la file d'attente pour l'API SSE
                phone_number = number['phone_number']
                if phone_number not in virtual_sms_queue:
                    virtual_sms_queue[phone_number] = []
                    
                virtual_sms_queue[phone_number].append({
                    'id': cursor.lastrowid,
                    'sender': sms['sender'],
                    'message': sms['message'],
                    'is_otp': sms['is_otp'],
                    'otp_code': otp_code,
                    'received_at': datetime.now().isoformat()
                })
                
                # Log de l'activité
                log_activity('virtual_number', 'sms_received', 
                            f"Numéro: {phone_number}", 
                            f"Expéditeur: {sms['sender']}, OTP: {'Oui' if sms['is_otp'] else 'Non'}")
        
        conn.close()
        
        # Attendre 30 secondes avant la prochaine simulation
        time.sleep(30)

@virtual_number_blueprint.route('/create', methods=['POST'])
def create_virtual_number():
    """Crée un nouveau numéro de téléphone virtuel"""
    country_code = request.json.get('country_code', '+33')  # Code pays par défaut: France
    
    # Générer un numéro aléatoire
    phone_number = country_code + ''.join(random.choice(string.digits) for _ in range(9))
    
    # Enregistrer dans la base de données
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO virtual_numbers (phone_number, provider) VALUES (?, ?)',
        (phone_number, 'simulation')
    )
    
    conn.commit()
    virtual_number_id = cursor.lastrowid
    conn.close()
    
    # Log de l'activité
    log_activity('virtual_number', 'create', phone_number)
    
    # Démarrer la simulation de SMS si ce n'est pas déjà fait
    global sms_simulation_running
    if not sms_simulation_running:
        simulation_thread = threading.Thread(target=simulate_incoming_sms)
        simulation_thread.daemon = True
        simulation_thread.start()
    
    return jsonify({
        'id': virtual_number_id,
        'phone_number': phone_number,
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    })

@virtual_number_blueprint.route('/list', methods=['GET'])
def list_virtual_numbers():
    """Liste tous les numéros virtuels disponibles"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, phone_number, provider, created_at, last_used FROM virtual_numbers')
    numbers = cursor.fetchall()
    
    conn.close()
    
    # Convertir les résultats en liste de dictionnaires
    result = []
    for number in numbers:
        result.append({
            'id': number['id'],
            'phone_number': number['phone_number'],
            'provider': number['provider'],
            'created_at': number['created_at'],
            'last_used': number['last_used']
        })
    
    return jsonify({
        'count': len(result),
        'numbers': result
    })

@virtual_number_blueprint.route('/<int:number_id>/sms', methods=['GET'])
def get_sms_for_number(number_id):
    """Récupère tous les SMS pour un numéro virtuel spécifique"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier que le numéro existe
    cursor.execute('SELECT phone_number FROM virtual_numbers WHERE id = ?', (number_id,))
    number = cursor.fetchone()
    
    if not number:
        conn.close()
        return jsonify({'error': 'Numéro virtuel non trouvé'}), 404
    
    # Récupérer les SMS
    cursor.execute('''
        SELECT id, sender, message, received_at, is_otp, otp_code 
        FROM received_sms 
        WHERE virtual_number_id = ? 
        ORDER BY received_at DESC
    ''', (number_id,))
    
    sms_list = cursor.fetchall()
    conn.close()
    
    # Convertir les résultats en liste de dictionnaires
    result = {
        'phone_number': number['phone_number'],
        'sms_count': len(sms_list),
        'sms': []
    }
    
    for sms in sms_list:
        result['sms'].append({
            'id': sms['id'],
            'sender': sms['sender'],
            'message': sms['message'],
            'received_at': sms['received_at'],
            'is_otp': bool(sms['is_otp']),
            'otp_code': sms['otp_code']
        })
    
    return jsonify(result)

@virtual_number_blueprint.route('/<int:number_id>/delete', methods=['POST'])
def delete_virtual_number(number_id):
    """Supprime un numéro virtuel et tous ses SMS associés"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier que le numéro existe
    cursor.execute('SELECT phone_number FROM virtual_numbers WHERE id = ?', (number_id,))
    number = cursor.fetchone()
    
    if not number:
        conn.close()
        return jsonify({'error': 'Numéro virtuel non trouvé'}), 404
    
    # Supprimer les SMS associés
    cursor.execute('DELETE FROM received_sms WHERE virtual_number_id = ?', (number_id,))
    
    # Supprimer le numéro
    cursor.execute('DELETE FROM virtual_numbers WHERE id = ?', (number_id,))
    
    conn.commit()
    conn.close()
    
    # Log de l'activité
    log_activity('virtual_number', 'delete', number['phone_number'])
    
    return jsonify({
        'success': True,
        'message': f'Numéro virtuel {number["phone_number"]} supprimé avec succès'
    })

@virtual_number_blueprint.route('/check-new-sms', methods=['POST'])
def check_new_sms():
    """Vérifie s'il y a de nouveaux SMS pour un numéro spécifique"""
    phone_number = request.json.get('phone_number')
    
    if not phone_number:
        return jsonify({'error': 'Numéro de téléphone non spécifié'}), 400
    
    # Récupérer les SMS en attente dans la file
    new_sms = virtual_sms_queue.get(phone_number, [])
    
    # Vider la file après récupération
    if phone_number in virtual_sms_queue:
        virtual_sms_queue[phone_number] = []
    
    return jsonify({
        'phone_number': phone_number,
        'new_sms_count': len(new_sms),
        'new_sms': new_sms
    })