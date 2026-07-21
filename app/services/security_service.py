"""
Security and encryption services.
"""
import logging
import re
from cryptography.fernet import Fernet
from flask import current_app

def encrypt_api_key(plaintext_key: str) -> bytes:
    """Encrypts an API key using the application encryption key."""
    encryption_key = current_app.config['ENCRYPTION_KEY']
    fernet = Fernet(encryption_key)
    return fernet.encrypt(plaintext_key.encode('utf-8'))

def decrypt_api_key(encrypted_key: bytes) -> str:
    """Decrypts an API key using the application encryption key."""
    encryption_key = current_app.config['ENCRYPTION_KEY']
    fernet = Fernet(encryption_key)
    return fernet.decrypt(encrypted_key).decode('utf-8')

class KeyRedactionFilter(logging.Filter):
    """Filters log records to redact API key patterns."""
    
    def __init__(self):
        super().__init__()
        # Matches AIza followed by 35 alphanumeric characters or dashes/underscores
        self.api_key_pattern = re.compile(r'AIza[0-9A-Za-z\-_]{35}')
        
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = self.api_key_pattern.sub('[REDACTED_API_KEY]', record.msg)
        elif isinstance(record.msg, bytes):
            # Convert to string just in case, though logging usually uses strings
            msg_str = record.msg.decode('utf-8', errors='ignore')
            record.msg = self.api_key_pattern.sub('[REDACTED_API_KEY]', msg_str)
            
        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self.api_key_pattern.sub('[REDACTED_API_KEY]', arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
            
        return True

def validate_key_format(key: str) -> bool:
    """Validates the format of a Google Gemini API key."""
    if not key or not isinstance(key, str):
        return False
    # Gemini API keys typically start with AIza and are 39 characters long
    pattern = re.compile(r'^AIza[0-9A-Za-z\-_]{35}$')
    return bool(pattern.match(key))
