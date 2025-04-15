# modules/sms_tools.py - Module d'outils SMS

from flask import Blueprint, request, jsonify, current_app
import requests
import random
import string
from twilio.rest import Client
from database import log_activity

sms_blueprint = Blueprint('sms_tools', __name__)

@sms_blueprint.route('/send-sms', methods=['POST'])
def send_sms():
    """Envoie un SMS via l'API Twilio"""
    to_number = request.json.get('to')
    message = request.json.get('message')
    
    if not to_number or not message:
        return jsonify({'error': 'Numéro de destination ou message non spécifié'}), 400
    
    # Log de l'activité (sans le message pour des raisons de confidentialité)
    log_activity('sms_tools', 'send_sms', to_number, "SMS envoyé")
    
    # Récupération des identifiants Twilio
    account_sid = current_app.config.get('TWILIO_ACCOUNT_SID', '')
    auth_token = current_app.config.get('TWILIO_AUTH_TOKEN', '')
    
    if not account_sid or not auth_token:
        return jsonify({'error': 'Configuration Twilio manquante'}), 500
    
    try:
        # Initialisation du client Twilio
        client = Client(account_sid, auth_token)
        
        # Envoi du SMS
        message = client.messages.create(
            body=message,
            from_='+15005550006',  # Numéro de test Twilio
            to=to_number
        )
        
        return jsonify({
            'success': True,
            'message_sid': message.sid,
            'status': message.status
        })
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'envoi du SMS: {str(e)}'}), 500

@sms_blueprint.route('/generate-otp', methods=['POST'])
def generate_otp():
    """Génère un OTP et l'envoie par SMS (optionnel)"""
    to_number = request.json.get('to')
    length = request.json.get('length', 6)
    send = request.json.get('send', False)
    
    # Validation
    if length < 4 or length > 10:
        return jsonify({'error': 'La longueur de l\'OTP doit être entre 4 et 10 caractères'}), 400
    
    # Génération de l'OTP
    otp = ''.join(random.choice(string.digits) for _ in range(length))
    
    # Log de l'activité
    log_activity('sms_tools', 'generate_otp', 
                 f"Longueur: {length}, Envoi: {send}", 
                 f"OTP généré: {otp}")
    
    # Si l'envoi est demandé
    if send and to_number:
        # Récupération des identifiants Twilio
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID', '')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN', '')
        
        if not account_sid or not auth_token:
            return jsonify({
                'otp': otp,
                'warning': 'Configuration Twilio manquante, SMS non envoyé'
            })
        
        try:
            # Initialisation du client Twilio
            client = Client(account_sid, auth_token)
            
            # Préparation et envoi du message
            message_text = f"Votre code de vérification est: {otp}"
            
            message = client.messages.create(
                body=message_text,
                from_='+15005550006',  # Numéro de test Twilio
                to=to_number
            )
            
            return jsonify({
                'otp': otp,
                'sent': True,
                'message_sid': message.sid,
                'status': message.status
            })
        except Exception as e:
            return jsonify({
                'otp': otp,
                'sent': False,
                'error': f'Erreur lors de l\'envoi du SMS: {str(e)}'
            })
    
    # Si aucun envoi n'est demandé, simplement retourner l'OTP
    return jsonify({
        'otp': otp,
        'sent': False
    })

@sms_blueprint.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Vérifie un OTP fourni par l'utilisateur"""
    user_otp = request.json.get('otp')
    expected_otp = request.json.get('expected_otp')
    
    if not user_otp or not expected_otp:
        return jsonify({'error': 'OTP utilisateur ou OTP attendu non spécifié'}), 400
    
    # Vérification de l'OTP
    verified = user_otp == expected_otp
    
    # Log de l'activité
    log_activity('sms_tools', 'verify_otp', 
                 "Vérification OTP", 
                 f"Résultat: {'Succès' if verified else 'Échec'}")
    
    return jsonify({
        'verified': verified,
        'message': 'OTP vérifié avec succès' if verified else 'OTP invalide'
    })