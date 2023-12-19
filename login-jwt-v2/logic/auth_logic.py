from flask import Blueprint, jsonify
from functions.database import cursor, conn
import bcrypt
import jwt
from datetime import datetime, timedelta
import pytz
import os

auth_blueprint = Blueprint('auth', __name__)

def register(request):
    data = request.get_json()
    username = data.get('username')
    password = data.get('password').encode('utf-8')  # mengubah ke byte
    
    cursor.execute("SELECT username, password FROM pengguna WHERE username=%s", (username,))
    user = cursor.fetchone()
    
    if user :
        return jsonify({'message': 'User already exist'})
    
    # Hash password using bcrypt
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
    
    cursor.execute("INSERT INTO pengguna (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
    conn.commit()
    
    return jsonify({'message': 'User berhasil terdaftar!'})

def login(request, app):
    auth = request.get_json()
    username = auth.get('username')
    password = auth.get('password').encode('utf-8')
    
    cursor.execute("SELECT username, password FROM pengguna WHERE username=%s", (username,))
    user = cursor.fetchone()
    
    if not user or not bcrypt.checkpw(password, user[1].encode('utf-8')):
        return jsonify({'message': 'Username atau password salah'}), 401
    
    # Ubah waktu ekspirasi dari UTC ke WIB
    utc_exp = datetime.utcnow() + timedelta(minutes=30)
    utc_timezone = pytz.timezone('UTC')
    wib_timezone = pytz.timezone('Asia/Jakarta')
    utc_exp = utc_timezone.localize(utc_exp)
    wib_exp = utc_exp.astimezone(wib_timezone)
    
    # Buat payload token dengan waktu ekspirasi dalam WIB
    payload = {
        'username': user[0],
        'exp': wib_exp
    }
    print(app.config['SECRET_KEY'])
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({'message': 'Login berhasil!', 'token': token, 'secret_key': app.config['SECRET_KEY'], 'data': payload})

def get_username(request, app):
    token = request.headers.get('Authorization')  # Mendapatkan token dari header Authorization

    if not token:
        return jsonify({'message': 'Token tidak ditemukan'}), 401

    # Ubah format token menjadi Bearer token jika belum dalam format tersebut
    if not token.startswith('Bearer '):
        return jsonify({'message': 'Format token tidak valid'}), 401

    token = token.split(' ')[1]  # Ambil bagian token setelah "Bearer "

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        username = decoded['username']
        # Lakukan sesuatu dengan username, misalnya dapatkan id
        cursor.execute("SELECT id, username FROM pengguna WHERE username=%s", (username,))
        user_info = cursor.fetchone()
        if not user_info:
            return jsonify({'message': 'Pengguna tidak ditemukan'}), 404
        user_id, username = user_info
        return jsonify({'id': user_id, 'username': username}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token sudah kadaluarsa'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token tidak valid', 'secret_key': app.config['SECRET_KEY']}), 401