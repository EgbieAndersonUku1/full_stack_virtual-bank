


from utils.security.encryption import Encryption

def generate_email_outbox_key():
    return Encryption.generate_key()



if __name__ == "__main__":
    print("[-] Generating key, please wait...")
    key = generate_email_outbox_key()
    print("[+] You can now copy your email outbox key")
    print(f"[+] Your email inbox key: {key}")

