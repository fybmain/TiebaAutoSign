import re
import html
import urllib.parse
from enum import Enum
from typing import List

from .request_adapter import RequestAdapter
from .model import Account


class TiebaAlreadySigned(Exception):
    pass


class SignResult(Enum):
    failed = '签到失败'
    already_signed = '已经签过'
    success = '签到成功'


class TiebaOperator:
    def __init__(self, account: Account):
        self.request_adapter = RequestAdapter()
        self.request_adapter.load_cookie_str(account.cookie)
        self.sign_url_prefix = None

    def fetch_favorite_tieba_list(self) -> List[str]:
        page_num = 1
        result = []

        while True:
            url = 'http://tieba.baidu.com/f/like/mylike?pn='+str(page_num)
            response_content = self.request_adapter.make_request(url).decode('GBK')
            regex = re.compile(r'title="(.+?)">\1</a></td>')
            name_list = re.findall(regex, response_content)
            result.extend(name_list)

            if response_content.find('下一页') < 0:
                break
            else:
                page_num += 1

        return result

    def fetch_sign_url_prefix(self) -> str:
        response_content = self.request_adapter.make_request_as_phone('http://tieba.baidu.com/mo/').decode('UTF-8')
        regex = re.compile(r'"([^"]+tab=favorite)"')
        link = re.search(regex, response_content).group(1)
        result = ('http://tieba.baidu.com' + html.unescape(link))[:-21]
        print('sign url prefix:', result)
        return result

    def prepare_sign(self):
        if self.sign_url_prefix is None:
            self.sign_url_prefix = self.fetch_sign_url_prefix()

    def get_tieba_sign_url(self, name: str):
        if self.sign_url_prefix is None:
            self.prepare_sign()

        url = self.sign_url_prefix + 'kw=' + urllib.parse.quote(name, encoding='UTF-8')
        response_content = self.request_adapter.make_request_as_phone(url).decode('UTF-8')
        regex = re.compile(r'mo/.+?">签到')
        result = regex.search(response_content)
        if result is None:
            raise TiebaAlreadySigned()
        else:
            return 'http://tieba.baidu.com/' + (html.unescape(result.group())[:-4])

    def sign_tieba(self, name: str) -> SignResult:
        if self.sign_url_prefix is None:
            self.prepare_sign()

        try:
            sign_url = self.get_tieba_sign_url(name)
        except TiebaAlreadySigned:
            return SignResult.already_signed

        response_content = self.request_adapter.make_request_as_phone(sign_url).decode('UTF-8')
        return SignResult.success
