import http.cookiejar
import urllib.request
import urllib.parse

from .model import Account


HTTP_REQUEST_INTERVAL = 3


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
        path="/",
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

    def load(self, account: Account):
        cookies = account.cookie
        for cookie_str in cookies.split(';'):
            name, value = cookie_str.split('=', 1)
            name.strip(' ')
            value.strip(' ')
            self.cookie_jar.set_cookie(make_cookie(name, value))

    def save(self, account: Account):
        cookie_str = ''
        for cookie in self.cookie_jar:
            if cookie.is_expired():
                pass
            else:
                cookie_str += cookie.name + '=' + cookie.value + ';'

        account.cookie = cookie_str

    def make_request(self, url: str, data: dict) -> bytes:
        result = self.opener.open(
            fullurl=url,
            data=urllib.parse.urlencode(data).encode()
        )
        return result.read()
