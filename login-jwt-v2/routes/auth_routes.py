from flask import Blueprint, jsonify, request, current_app
from logic.auth_logic import register, login, get_username

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/register', methods=['POST'])
def register_route():
    return register(request)

@auth_blueprint.route('/login', methods=['POST'])
def login_route():
    return login(request, current_app)

@auth_blueprint.route('/get_username', methods=['GET'])
def get_username_route():
    return get_username(request, current_app)
