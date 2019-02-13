import re
import html
import urllib.parse
from enum import Enum
from typing import List, Optional

from .request_adapter import RequestAdapter
from .model import Account


RETRY_LIMIT = 10


class TiebaState(Enum):
    unknown = '未知状态'
    unlike = '未关注'
    unsigned = '未签到'
    signed = '已签到'


class SignResult(Enum):
    unknown_error = '未知错误'
    network_error = '网络错误'

    not_liked = '未关注'
    success = '签到成功'
    already_signed = '已经签过'


class TiebaOperator:
    like_regex = re.compile(r'href="(/mo/.+?)">喜欢本吧')
    sign_regex = re.compile(r'href="(/mo/.+?)">签到')
    signed_regex = re.compile(r'>已签到<')

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

    def _get_tieba_url(self, name: str) -> str:
        return self.sign_url_prefix + 'kw=' + urllib.parse.quote(name, encoding='UTF-8')

    def _get_tieba_state(self, webpage: str) -> TiebaState:
        like_url_match = self.like_regex.search(webpage)
        if like_url_match is not None:
            return TiebaState.unlike

        sign_url_match = self.sign_regex.search(webpage)
        if sign_url_match is not None:
            return TiebaState.unsigned

        signed_match = self.signed_regex.search(webpage)
        if signed_match is not None:
            return TiebaState.signed

        return TiebaState.unknown

    def _get_sign_url(self, webpage: str) -> str:
        sign_url_match = self.sign_regex.search(webpage)
        assert(sign_url_match is not None)
        return 'http://tieba.baidu.com' + html.unescape(sign_url_match.group(1))

    def _fetch_sign_url_prefix(self) -> str:
        response_content = self.request_adapter.make_request_as_phone('http://tieba.baidu.com/mo/').decode('UTF-8')
        regex = re.compile(r'"([^"]+tab=favorite)"')
        link = re.search(regex, response_content).group(1)
        result = ('http://tieba.baidu.com' + html.unescape(link))[:-21]
        return result

    def prepare_phone(self):
        if self.sign_url_prefix is None:
            self.sign_url_prefix = self._fetch_sign_url_prefix()

    def sign_tieba(self, name: str) -> SignResult:
        self.prepare_phone()

        tieba_url = self._get_tieba_url(name)
        sign_url = None

        need_sign = False
        retry_counter = 0
        while retry_counter < RETRY_LIMIT:
            if sign_url is not None:
                tieba_webpage = self.request_adapter.make_request_as_phone(sign_url).decode('UTF-8')
            else:
                tieba_webpage = self.request_adapter.make_request_as_phone(tieba_url).decode('UTF-8')

            retry_counter += 1

            tieba_state = self._get_tieba_state(webpage=tieba_webpage)

            if tieba_state == TiebaState.unknown:
                sign_url = None
            elif tieba_state == TiebaState.unlike:
                return SignResult.not_liked
            elif tieba_state == TiebaState.unsigned:
                need_sign = True
                sign_url = self._get_sign_url(webpage=tieba_webpage)
            elif tieba_state == TiebaState.signed:
                if need_sign:
                    return SignResult.success
                else:
                    return SignResult.already_signed

        return SignResult.unknown_error
