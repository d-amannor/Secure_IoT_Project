import hmac
import hashlib


# hmackey_hex = bytes.fromhex('0f0e0d0c0b0a09080706050403020100')

def verify_hmac(hmackey , message, received_hmac):
    hmackey_hex = bytes.fromhex(hmackey)
    generated_hmac = hmac.new(hmackey_hex, message.encode('utf-8'), hashlib.sha256).hexdigest()

    if generated_hmac == received_hmac:
        return True
    else:
        return False

def split_input_string(input_string):
    parts = input_string.split('|')
    if len(parts) != 3:
        return "0","0","0"

    return parts[0], parts[1], parts[2]

def verify_challenge(msg_input):
    ciphertext , hmac_text , nonce = split_input_string(msg_input)

    hmackey = '0f0e0d0c0b0a0908070605040302bcfe'
    if verify_hmac(hmackey , ciphertext, hmac_text):
        return ciphertext , nonce
    else:
        return None, None


def main():
    inputmsg = "MGMgOGUgZTMgNmEgNjQgNGUgZDcgYTIgZmQgMmUgMzQgNDkgNGQgNDQgNDEgMDAgNzYgNjkgNzEgMzkgYTcgMmEgOTYgOGQgYjggY2IgOTYgNTQgNTIgZmIgZGMgMTkgNDAgZWQgNDIgOGQgMmMgNjkgMWQgZGYgN2QgY2EgMTYgMTUgNGQgNzAgOTUgMmIg|10e000b404939995fe7cbbcfb11510171042e45dca5b08e9f5e221a5238a4f8e|FAD9FCAB5F13F44D521E0D40E81DBD3D"
    
    cipher,nonce = verify_challenge(inputmsg)
    print(f'cipher: {cipher} \nNonce: {nonce}')

if __name__ == "__main__":
    main()
