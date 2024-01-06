import os

from allauth.account.adapter import DefaultAccountAdapter


class MyAccountAdapter(DefaultAccountAdapter):
    def __init__(self, request=None):
        super().__init__(request)

    def get_login_redirect_url(self, request):
        # リダイレクトするurl
        if os.path.exists("local.py"):
            return "http://127.0.0.1:8000/mypage"
        else:
            return "https://jbsl-web.herokuapp.com/mypage"
