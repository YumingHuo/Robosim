import hashlib

password = "222"
hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()

print(hashed_password)
