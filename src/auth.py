import os
import json
import base64
import inquirer
import requests
from dotenv import load_dotenv

class DevOpsAuth:
    def __init__(self):
        self.pat = None
        self.headers = None
        self.organization = None
        load_dotenv()
        self._load_user_config()

    def _load_user_config(self):
        """ユーザー設定を読み込みます。存在しない場合はdefault_config.jsonから作成します。"""
        try:
            with open('user_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.organization = config.get('organization', '')
        except FileNotFoundError:
            # user_config.jsonが存在しない場合、default_config.jsonから作成
            try:
                with open('default_config.json', 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError("default_config.jsonが見つかりません。")
            
            # デフォルト設定でuser_config.jsonを作成
            with open('user_config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            self.organization = default_config.get('organization', '')

    def _save_user_config(self):
        """ユーザー設定を保存します。"""
        try:
            with open('user_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            # user_config.jsonが存在しない場合、default_config.jsonから作成
            try:
                with open('default_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError("default_config.jsonが見つかりません。")
        
        config['organization'] = self.organization
        
        with open('user_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_organization(self):
        """組織名を取得します。"""
        if not self.organization:
            self.organization = self._get_organization_from_user()
            self._save_user_config()
        return self.organization

    def _get_organization_from_user(self):
        """ユーザーから組織名を取得します。"""
        while True:
            questions = [
                inquirer.Text('organization',
                            message='Azure DevOps組織名を入力してください')
            ]
            answers = inquirer.prompt(questions)
            org = answers['organization']
            
            if self._validate_organization(org):
                return org
            print("無効な組織名です。再度入力してください。")

    def _validate_organization(self, organization):
        """組織名の有効性を検証します。"""
        headers = self.get_auth_headers()
        try:
            response = requests.get(
                f"https://dev.azure.com/{organization}/_apis/projects?api-version=7.0",
                headers=headers
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

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
            questions = [
                inquirer.Password('pat',
                                message='Azure DevOps Personal Access Tokenを入力してください',
                                validate=lambda _, x: len(x) > 0)
            ]
            answers = inquirer.prompt(questions)
            pat = answers['pat']
            
            if self._validate_pat(pat):
                # 検証成功したらPATを環境変数に保存
                with open('.env', 'a') as f:
                    f.write(f'\nDEVOPS_PAT={pat}')
                return pat
            print("無効なトークンです。再度入力してください。")

    def _validate_pat(self, pat):
        """PATの有効性を検証します。"""
        headers = self._create_headers(pat)
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
            auth_string = base64.b64encode(f":{pat}".encode('utf-8')).decode('utf-8')
            self.headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
        return self.headers 