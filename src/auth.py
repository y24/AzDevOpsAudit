import os
import base64
import requests
from dotenv import load_dotenv

class DevOpsAuth:
    def __init__(self):
        self.pat = None
        self.headers = None
        load_dotenv()

    def get_auth_headers(self):
        """認証ヘッダーを取得します。"""
        if self.headers:
            return self.headers

        self.pat = os.getenv('DEVOPS_PAT')
        if not self.pat:
            self.pat = self._get_pat_from_user()
        
        return self._create_headers(self.pat)

    def _get_pat_from_user(self):
        """ユーザーからPATを取得し、検証します。"""
        while True:
            pat = input("Azure DevOps Personal Access Tokenを入力してください: ")
            if self._validate_pat(pat):
                # 検証成功したらPATを環境変数に保存
                with open('.env', 'a') as f:
                    f.write(f'\nDEVOPS_PAT={pat}')
                return pat
            print("無効なトークンです。再度入力してください。")

    def _validate_pat(self, pat):
        """PATの有効性を検証します。"""
        headers = self._create_headers(pat)
        # Azure DevOps APIの簡単なエンドポイントを呼び出してテスト
        try:
            response = requests.get(
                "https://dev.azure.com/_apis/projects?api-version=7.0",
                headers=headers
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _create_headers(self, pat):
        """認証ヘッダーを生成します。"""
        if not self.headers:
            auth_string = base64.b64encode(f":{pat}".encode()).decode()
            self.headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
        return self.headers 