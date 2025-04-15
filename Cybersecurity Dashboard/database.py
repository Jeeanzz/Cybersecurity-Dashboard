# database.py - Module de gestion de la base de données

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'cybersec_tools.db'

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    if not os.path.exists(DATABASE_PATH):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Table pour les logs d'activité
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            input_data TEXT,
            result_summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table pour les numéros virtuels
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS virtual_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            provider TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME
        )
        ''')
        
        # Table pour les SMS reçus
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS received_sms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            virtual_number_id INTEGER,
            sender TEXT,
            message TEXT,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_otp BOOLEAN DEFAULT 0,
            otp_code TEXT,
            FOREIGN KEY (virtual_number_id) REFERENCES virtual_numbers (id)
        )
        ''')
        
        # Table pour les résultats de scan réseau
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT NOT NULL,
            target TEXT NOT NULL,
            results TEXT,
            scan_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        print("Base de données initialisée avec succès.")

def log_activity(module, action, input_data=None, result_summary=None):
    """Enregistre une activité dans les logs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO activity_logs (module, action, input_data, result_summary) VALUES (?, ?, ?, ?)',
        (module, action, input_data, result_summary)
    )
    
    conn.commit()
    conn.close()