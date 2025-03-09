import hmac
import hashlib
import base64

def calculate_secret_hash(client_id, client_secret, username):
    message = username + client_id
    dig = hmac.new(
        client_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode('utf-8')

# Replace these with your actual values
client_id = '4ij22djf41buoullmg091gvbhm'
client_secret = '1ck0ihrf79fb29nc9jar4adaad9k83b4oen9hbio2kvse4be5l53'
username = 'testuser'

secret_hash = calculate_secret_hash(client_id, client_secret, username)
print(f'SECRET_HASH: {secret_hash}')
