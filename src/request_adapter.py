import time
import datetime
from typing import Optional

import http.cookiejar
import urllib.request
import urllib.parse


HTTP_REQUEST_INTERVAL = 3
PHONE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 UBrowser/6.1.2107.204 Safari/537.36'


def make_cookie(name, value):
    cookie=http.cookiejar.Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain='baidu.com',
        domain_specified=True,
        domain_initial_dot=False,
        path='/',
        path_specified=True,
        secure=False,
        expires=None,
        discard=False,
        comment=None,
        comment_url=None,
        rest=None
    )
    return cookie


class RequestAdapter:
    def __init__(self):
        self.last_request_time = None

        self.cookie_jar = http.cookiejar.CookieJar()
        self.cookie_processor = urllib.request.HTTPCookieProcessor(self.cookie_jar)
        self.opener = urllib.request.build_opener(self.cookie_processor, urllib.request.HTTPHandler)

    def load_cookie_str(self, cookie_str: str):
        for cookie in cookie_str.split(';'):
            name, value = cookie.split('=', 1)
            name.strip(' ')
            value.strip(' ')
            self.cookie_jar.set_cookie(make_cookie(name, value))

    def get_cookie_str(self) -> str:
        cookie_str = ''
        for cookie in self.cookie_jar:
            if cookie.is_expired():
                pass
            else:
                cookie_str += cookie.name + '=' + cookie.value + ';'

        return cookie_str

    def make_request(self, url: str, data: Optional[dict] = None, headers: dict = {}) -> bytes:
        if data is None:
            encoded_data = None
        else:
            encoded_data = urllib.parse.urlencode(data).encode()

        if not (self.last_request_time is None):
            assert isinstance(self.last_request_time, datetime.datetime)
            current_time = datetime.datetime.now()
            delta_seconds = (current_time - self.last_request_time).total_seconds()
            if delta_seconds < HTTP_REQUEST_INTERVAL:
                time.sleep(delta_seconds)

        request = urllib.request.Request(
            url=url,
            data=encoded_data,
            headers=headers
        )
        response = self.opener.open(request)
        self.last_request_time = datetime.datetime.now()

        result = response.read()
        return result

    def make_request_as_phone(self, url: str, data: Optional[dict] = None, headers: dict = {}) -> bytes:
        user_agent_header = {
            'User-Agent': PHONE_USER_AGENT,
        }
        headers = dict(headers, **user_agent_header)
        return self.make_request(url, data, headers)
