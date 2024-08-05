#!/usr/bin/env python3
import sys
import os
import requests
import random
import pathlib

from checklib import *
from passvault_lib import *
from pathlib import Path

BASE_DIR = Path(__file__).absolute().resolve().parent

class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests.exceptions.ConnectionError')

    def check(self):
        session = self.get_initialized_session()
        username, password = rnd_username(), rnd_password() 

        PATH = pathlib.Path(__file__).parent.resolve()
        with open(f'{PATH}/websites.txt', 'r') as f:
            lines = f.readlines()
        if not lines:
            print("ERROR!!!!!! The websites file is empty or all lines are blank.")
            return
            
        website = random.choice(lines).strip()

        self.mch.register(session, username, password)
        self.mch.login(session, username, password, Status.MUMBLE)
        random_password = rnd_password()
        created_password = self.mch.add_password(session, website=website, username=username, password=random_password, status=Status.MUMBLE)

        data = self.mch.get_password(session, password_id=created_password["id"], status=Status.MUMBLE)
        self.assert_eq(data["website"], website, "Website value is invalid", Status.CORRUPT)
        self.assert_eq(data["username"], username, "Website value is invalid", Status.CORRUPT)
        self.assert_eq(data["password"], random_password, "Website value is invalid", Status.CORRUPT)
        self.cquit(Status.OK)

        #check if registered+logined, password is created and is not replaced with fake one


    def put(self, flag_id: str, flag: str, vuln: str):
        session = self.get_initialized_session()
        username, password = rnd_username(), rnd_password() 
        self.mch.register(session, username, password)
        self.mch.login(session, username, password, Status.MUMBLE)

        if vuln == "1":
            PATH = pathlib.Path(__file__).parent.resolve()
            with open(f'{PATH}/websites.txt', 'r') as f:
                lines = f.readlines()
            if not lines:
                print("ERROR!!!!!! The websites file is empty or all lines are blank.")
                return
            
            website = random.choice(lines).strip()
            created_password = self.mch.add_password(session, website=website, username=username, password=flag, status=Status.MUMBLE)
            password_id = created_password["id"]

        self.cquit(Status.OK, f"{username}", f'{username}:{password}:{password_id}')

    def get(self, flag_id: str, flag: str, vuln: str):
        session = self.get_initialized_session()
        username, password, password_id = flag_id.split(':')
        password_id = int(password_id)
        self.mch.login(session, username, password, Status.CORRUPT)
        data = self.mch.get_password(session, password_id=password_id, status=Status.CORRUPT)
        if vuln == "1":
            self.assert_eq(data["password"], flag, "Password(secret) value is invalid (flag was not found)", Status.CORRUPT)
        self.cquit(Status.OK)
        # check that flag is still in password after some time

if __name__ == '__main__':
    c = Checker(sys.argv[2])
    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
