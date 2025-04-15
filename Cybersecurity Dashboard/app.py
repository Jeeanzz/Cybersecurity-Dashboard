# app.py - Fichier principal de l'application Flask

from flask import Flask, render_template, jsonify, request
from modules.ip_analyzer import ip_blueprint
from modules.port_scanner import port_blueprint
from modules.dns_resolver import dns_blueprint
from modules.network_analyzer import network_blueprint
from modules.reverse_ip import reverse_ip_blueprint
from modules.osint_tools import osint_blueprint
from modules.sms_tools import sms_blueprint
from modules.virtual_number import virtual_number_blueprint
import os

app = Flask(__name__)

# Enregistrement des blueprints pour chaque module
app.register_blueprint(ip_blueprint, url_prefix='/api/ip')
app.register_blueprint(port_blueprint, url_prefix='/api/ports')
app.register_blueprint(dns_blueprint, url_prefix='/api/dns')
app.register_blueprint(network_blueprint, url_prefix='/api/network')
app.register_blueprint(reverse_ip_blueprint, url_prefix='/api/reverse-ip')
app.register_blueprint(osint_blueprint, url_prefix='/api/osint')
app.register_blueprint(sms_blueprint, url_prefix='/api/sms')
app.register_blueprint(virtual_number_blueprint, url_prefix='/api/virtual-number')

# Route principale qui sert l'interface utilisateur
@app.route('/')
def index():
    return render_template('index.html')

# Configuration et chargement des clés API depuis les variables d'environnement
app.config['SHODAN_API_KEY'] = os.environ.get('SHODAN_API_KEY', '')
app.config['IPINFO_API_KEY'] = os.environ.get('IPINFO_API_KEY', '')
app.config['HIBP_API_KEY'] = os.environ.get('HIBP_API_KEY', '')
app.config['TWILIO_ACCOUNT_SID'] = os.environ.get('TWILIO_ACCOUNT_SID', '')
app.config['TWILIO_AUTH_TOKEN'] = os.environ.get('TWILIO_AUTH_TOKEN', '')

# Initialisation de la base de données
from database import init_db
init_db()

if __name__ == '__main__':
    app.run(debug=True)