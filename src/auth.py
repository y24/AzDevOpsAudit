import os
import json
import base64
import getpass
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

    def setup_and_validate_connection(self):
        """認証情報を設定します。"""
        # PATの取得
        self.pat = os.getenv('DEVOPS_PAT')
        if not self.pat:
            self.pat = self._get_pat_from_user()

        # 組織名の取得（user_config.jsonから既に読み込まれている）
        if not self.organization:
            print("user_config.jsonに組織名が設定されていません。")
            self.organization = self._get_organization_from_user()
            self._save_user_config()

        # ヘッダーを設定
        self.headers = self._create_headers()

    def get_auth_headers(self):
        """認証ヘッダーを取得します。"""
        if not self.headers:
            raise ValueError("認証が完了していません。setup_and_validate_connection()を先に実行してください。")
        return self.headers

    def get_organization(self):
        """組織名を取得します。"""
        if not self.organization:
            raise ValueError("認証が完了していません。setup_and_validate_connection()を先に実行してください。")
        return self.organization

    def _get_organization_from_user(self):
        """ユーザーから組織名を取得します。"""
        questions = [
            inquirer.Text('organization',
                        message='Azure DevOps組織名を入力してください')
        ]
        answers = inquirer.prompt(questions)
        return answers['organization']

    def _get_pat_from_user(self):
        """ユーザーからPATを取得します。"""
        print("Azure DevOps Personal Access Tokenを入力してください")
        while True:
            pat = getpass.getpass(prompt='PAT: ')
            if pat.strip():  # 空でないことを確認
                break
            print("PATを入力してください。")

        # 新しいPATを環境変数ファイルに保存
        with open('.env', 'a') as f:
            f.write(f'\nDEVOPS_PAT={pat}')
        return pat

    def _create_headers(self):
        """認証ヘッダーを生成します。"""
        auth_string = base64.b64encode(f":{self.pat}".encode('utf-8')).decode('utf-8')
        return {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        } 