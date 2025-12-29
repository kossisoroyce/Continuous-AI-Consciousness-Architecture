"""
Data Encryption Manager
Provides encryption at rest and in transit
AES-256-GCM for symmetric encryption
"""
import os
import base64
import secrets
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class EncryptionManager:
    """
    Handles data encryption/decryption for HMT platform
    Uses AES-256-GCM for authenticated encryption
    """
    
    def __init__(self, master_key: bytes = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: 32-byte master encryption key. If None, generates new key.
        """
        if master_key is None:
            # Try to load from environment or generate new
            env_key = os.getenv("HMT_ENCRYPTION_KEY")
            if env_key:
                self.master_key = base64.b64decode(env_key)
            else:
                self.master_key = secrets.token_bytes(32)
                print(f"[SECURITY] Generated new encryption key. Store this securely:")
                print(f"HMT_ENCRYPTION_KEY={base64.b64encode(self.master_key).decode()}")
        else:
            self.master_key = master_key
        
        self._aesgcm = AESGCM(self.master_key)
    
    def derive_key(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2
        
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    def encrypt(self, plaintext: bytes, associated_data: bytes = None) -> bytes:
        """
        Encrypt data using AES-256-GCM
        
        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (not encrypted but authenticated)
        
        Returns:
            nonce (12 bytes) + ciphertext + tag
        """
        nonce = secrets.token_bytes(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext
    
    def decrypt(self, ciphertext: bytes, associated_data: bytes = None) -> bytes:
        """
        Decrypt data using AES-256-GCM
        
        Args:
            ciphertext: nonce (12 bytes) + encrypted data + tag
            associated_data: Additional authenticated data
        
        Returns:
            Decrypted plaintext
        """
        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]
        return self._aesgcm.decrypt(nonce, actual_ciphertext, associated_data)
    
    def encrypt_string(self, plaintext: str, associated_data: str = None) -> str:
        """Encrypt string and return base64-encoded result"""
        aad = associated_data.encode() if associated_data else None
        encrypted = self.encrypt(plaintext.encode(), aad)
        return base64.b64encode(encrypted).decode()
    
    def decrypt_string(self, ciphertext: str, associated_data: str = None) -> str:
        """Decrypt base64-encoded ciphertext"""
        aad = associated_data.encode() if associated_data else None
        encrypted = base64.b64decode(ciphertext)
        decrypted = self.decrypt(encrypted, aad)
        return decrypted.decode()
    
    def encrypt_field(self, value: any, field_name: str) -> str:
        """
        Encrypt a database field with field name as AAD
        Provides binding between encrypted data and its context
        """
        import json
        plaintext = json.dumps(value)
        return self.encrypt_string(plaintext, field_name)
    
    def decrypt_field(self, ciphertext: str, field_name: str) -> any:
        """Decrypt a database field"""
        import json
        plaintext = self.decrypt_string(ciphertext, field_name)
        return json.loads(plaintext)
    
    def hash_sensitive(self, data: str) -> str:
        """
        One-way hash for sensitive data (e.g., for lookups)
        Uses SHA-256 with salt
        """
        salt = self.master_key[:16]  # Use part of master key as salt
        return hashlib.pbkdf2_hmac(
            'sha256', 
            data.encode(), 
            salt, 
            100000
        ).hex()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key (base64 encoded)"""
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode()

class FieldEncryption:
    """
    Decorator/utility for encrypting specific model fields
    """
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.em = encryption_manager
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list) -> dict:
        """Encrypt specified fields in a dictionary"""
        result = data.copy()
        for field in fields_to_encrypt:
            if field in result and result[field] is not None:
                result[field] = self.em.encrypt_field(result[field], field)
        return result
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list) -> dict:
        """Decrypt specified fields in a dictionary"""
        result = data.copy()
        for field in fields_to_decrypt:
            if field in result and result[field] is not None:
                try:
                    result[field] = self.em.decrypt_field(result[field], field)
                except Exception:
                    pass  # Field might not be encrypted
        return result

# Sensitive fields that should be encrypted at rest
SENSITIVE_FIELDS = [
    'api_key',
    'password',
    'operator_notes',
    'mission_details',
    'location_data',
    'personal_info',
    'ai_reasoning',  # For classified missions
]

# Global encryption manager (initialized lazily)
_encryption_manager: Optional[EncryptionManager] = None

def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
