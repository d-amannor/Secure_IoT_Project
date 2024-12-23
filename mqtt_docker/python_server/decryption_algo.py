import argparse
from speck import SpeckCipher
import base64

# Define the 128-bit key used in Arduino code
key = 0x0f0e0d0c0b0a09080706050403020100  # Convert the key to a 16-byte integer

# Function to convert hex string to bytes
def hex_to_bytes(hex_str):
    return bytes(int(x, 16) for x in hex_str.split())

# Initialize the SpeckCipher object
speck = SpeckCipher(key, key_size=128, block_size=128)

# Decrypt function
def decrypt_speck(speck, cipher_text):
    block_size = 16  # Speck128 block size in bytes
    plain_text = b""

    # Decrypt each block
    for i in range(0, len(cipher_text), block_size):
        block = cipher_text[i:i + block_size]
        # Convert block to integer for decryption
        block_int = int.from_bytes(block, byteorder="big")
        decrypted_block_int = speck.decrypt(block_int)
        # Convert decrypted integer block back to bytes
        decrypted_block = decrypted_block_int.to_bytes(block_size, byteorder="big")
        plain_text += decrypted_block

    return plain_text

def remove_padding(data):
    # Remove trailing zeros added as padding
    return data.rstrip(b'\x00').decode('utf-8')  # Decode only after padding removal

def decrypt_msg(secret):
    decode_cipherB64 = base64.b64decode(secret)
    cipher_text = hex_to_bytes(decode_cipherB64)

    # Perform decryption
    plain_text = decrypt_speck(speck, cipher_text)
    
    decrypted_text = remove_padding(plain_text)
    
    return decrypted_text
    
    
    
def main():
    parser = argparse.ArgumentParser(description="Decrypt SPECK128 ciphertext.")
    parser.add_argument('-c', '--ciphertext', required=True, help="Ciphertext in hexadecimal format.")
    args = parser.parse_args()
    
    # Decode Base64
    decode_cipherB64 = base64.b64decode(args.ciphertext)
    # Convert the provided ciphertext to bytes
    cipher_text = hex_to_bytes(decode_cipherB64)

    # Perform decryption
    plain_text = decrypt_speck(speck, cipher_text)

    # Print decrypted text before and after removing padding
    print("Decrypted Text (raw bytes):", plain_text)

    # Remove padding and decode to string
    decrypted_text = remove_padding(plain_text)
    print("Decrypted Text (decoded):", decrypted_text)

if __name__ == "__main__":
    main()
