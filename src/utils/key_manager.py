import os
import base64

def get_decrypted_key(env_var_name="APP_SECRET_TOKEN", fallback_env_var_name="GOOGLE_API_KEY"):
    """
    Retrieves and decrypts the API key from the environment variable.
    The encryption scheme is: Base64 encode -> Reverse string.
    So decryption is: Reverse string -> Base64 decode.
    """
    token = os.getenv(env_var_name)
    if not token:
       
        return os.getenv(fallback_env_var_name)

    try:
        reversed_token = token[::-1]
        decoded_bytes = base64.b64decode(reversed_token)
        return decoded_bytes.decode('utf-8')
    except Exception:
        return token
