from pyargon2 import hash
import os
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad
import base64


def encrypt(data, key, iv, salt):
    hex_encoded_hash = hash(key, salt.hex())
    aes_key = bytes.fromhex(hex_encoded_hash)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder='big')
    pad_data = pad(byte_data, AES.block_size)
    ciphertext = cipher.encrypt(pad_data)
    ciphertext_binary = ''.join(format(byte, '08b') for byte in ciphertext)
    return ciphertext_binary


def decrypt(data, key, iv, salt):
    iv_bytes = int(iv, 2).to_bytes((len(iv) + 7) // 8, byteorder='big')
    salt_bytes = int(salt, 2).to_bytes((len(salt) + 7) // 8, byteorder='big')

    hex_encoded_hash = hash(key, salt_bytes.hex())
    aes_key = bytes.fromhex(hex_encoded_hash)
    decipher = AES.new(aes_key, AES.MODE_CBC, iv_bytes)
    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder='big')
    decrypted_data = decipher.decrypt(byte_data)
    plaintext = unpad(decrypted_data, AES.block_size)
    plaintext_binary = ''.join(format(byte, '08b') for byte in plaintext)
    return plaintext_binary
