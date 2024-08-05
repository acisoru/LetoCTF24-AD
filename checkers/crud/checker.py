#!/usr/bin/env python3
import socket
import sys
import random
import string

import requests
from checklib import *


def print(*args, **kwargs): pass  # disable print


def generate_random_datastring(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string


def percent_50():
    return random.randint(1, 2) == 1


class TcpClient:
    def __init__(self, host='localhost', port=6767):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.sock.recv(1024 * 1024)
            print(f"Connected to {self.host}:{self.port}")
        except ConnectionError as e:
            print(f"Failed to connect to {self.host}:{self.port}: {e}")
            return False
        return True

    def send_recv(self, message):
        try:
            self.sock.sendall(message.encode('utf-8'))
            response = self.sock.recv(1024 * 1024).decode('utf-8')
            return response
        except socket.error as e:
            print(f"Error sending message: {e}")
            return "Error"

    def auth(self, token):
        response = self.send_recv(f"auth {token}\n")
        return response

    def auth_check(self, token):
        return self.auth(token).startswith(f'Authentication successful. Token set to: {token}')

    def help(self):
        response = self.send_recv("help\n")
        return response

    def append(self, value):
        response = self.send_recv(f"append {value}\n")
        return response.split(' ')[-1][:-2]

    def get(self, index):
        response = self.send_recv(f"get {index}\n").strip().split('"')[-2].strip()
        return response

    def set(self, index, value):
        response = self.send_recv(f"set {index} {value}\n")
        return response

    def size(self):
        response = self.send_recv("size\n")
        return response

    def print_all(self):
        response = self.send_recv("print\n").strip()
        return response

    def exit(self):
        response = self.send_recv("exit\n")
        return response

    def close(self):
        self.sock.close()
        print("Connection closed.")


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests.exceptions.ConnectionError')

    def check(self):
        client = TcpClient(host=self.host, port=6767)
        client.connect()
        for _ in range(random.randint(2, 5)):
            self.assert_eq(client.auth_check(generate_random_datastring(random.randint(10, 30))), True, "Auth error",
                           Status.MUMBLE)
            for _ in range(random.randint(1, 7)):
                tgt_set = generate_random_datastring(random.randint(10, 30))
                if percent_50():
                    dat_idx = client.append(tgt_set)
                else:
                    dat_idx = client.append(generate_random_datastring(random.randint(10, 30)))
                    client.set(dat_idx, tgt_set)

                if percent_50():
                    data_retrieved = client.get(dat_idx)
                    self.assert_eq(tgt_set, data_retrieved, "Data get&put error", Status.MUMBLE)
                else:
                    data_retrieved = client.print_all()
                    self.assert_in(tgt_set, data_retrieved, "Data get&put error", Status.MUMBLE)

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        client = TcpClient(host=self.host, port=6767)
        client.connect()
        auth_tkn = generate_random_datastring(random.randint(10, 30))
        client.auth(auth_tkn)

        if vuln == "1":
            if percent_50():
                flag_index = client.append(flag)
            else:
                flag_index = client.append(generate_random_datastring(random.randint(10, 30)))
                client.set(flag_index, flag)

        self.cquit(Status.OK, f"{flag_index}", f"{auth_tkn}:{flag_index}")

    def get(self, flag_id: str, flag: str, vuln: str):
        print('get FLAG by!', flag_id, '!!<-id')
        client = TcpClient(host=self.host, port=6767)
        client.connect()
        auth_tkn = flag_id.split(':')[0]
        client.auth(auth_tkn)
        if vuln == "1":
            if percent_50():
                flag_retrieved = client.get(flag_id.split(':')[1])
                self.assert_eq(flag, flag_retrieved, "Incorrect flag", Status.CORRUPT)
            else:
                data_retrieved = client.print_all()
                self.assert_in(flag, data_retrieved, "Incorrect flag", Status.CORRUPT)

        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])
    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)

# if __name__ == '__main__':
#     c = Checker("127.0.0.1")
#     try:
#         # c.action("put", "", "TestFLAG234Fofkdjfn", "1")
#         # c.action("get", "m740S5HMvflTqqZMR8X9Lb3CWRj:57", "FFF", "1")
#         c.action("check")
#     except c.get_check_finished_exception():
#         cquit(Status(c.status), c.public, c.private)
