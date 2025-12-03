import base64
import sys

def encrypt_key(key):
    if not key:
        return ""
    encoded_bytes = base64.b64encode(key.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')

    return encoded_str[::-1]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        key = sys.argv[1]
    else:
        key = input("Enter your Google API Key: ").strip()
    
    encrypted = encrypt_key(key)
    print(f"\nOriginal Key: {key}")
    print(f"Encrypted Token: {encrypted}")
    print(f"\nAdd this to your docker-compose.yml or .env:")
    print(f"APP_SECRET_TOKEN={encrypted}")
