import requests

from checklib import *

PORT = 8888

class CheckMachine:
    @property
    def url(self) -> str:
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def register(self, session: requests.Session, username: str, password: str):
        url = f'{self.url}/api/register'
        response = session.post(url, json={
            "username": username,
            "password": password
        })
        self.c.assert_eq(200, response.status_code, "invalid response code on registration")	

    def login(self, session: requests.Session, username: str, password: str, status: Status):
        url = f'{self.url}/api/login'
        response = session.post(url, json={
            "username": username,
            "password": password
        })
        self.c.assert_neq(session.cookies.get("access_token"), None, "Auth cookie(access_token) were not set on login")
        self.c.assert_eq(200, response.status_code, "invalid response code on login", status)

    def add_password(self, session: requests.Session, website: str, username: str, password: str, status: Status):
        url = f'{self.url}/api/passwords'
        data = {
            "website": website,
            "username": username,
            "password": password
        }
        response = session.post(url, json=data)
        self.c.assert_eq(200, response.status_code, "Failed to add new password", status)
        return self.c.get_json(response, "Invalid response on adding new password", status)

    def get_password(self, session: requests.Session, password_id: int, status: Status) -> dict: 
        url = f'{self.url}/api/passwords'
        response = session.get(url)
        data = self.c.get_json(response, "Invalid response on getting poassword", status)
        self.c.assert_eq(type(data), list, "Invalid response on getting reqpoassworduest", status)
        data = next((password for password in data if password['id'] == password_id), None)
        self.c.assert_neq(data, None, "Post was not found on account", status)
        url = f'{self.url}/api/passwords/{password_id}'
        response = session.get(url)
        data = self.c.get_json(response, "Invalid response on getting poassword", status)
        self.c.assert_eq(data['id'], password_id, "Invalid password(password_id) returned", status)
        return data
