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
        """認証情報を設定し、接続を検証します。"""
        # PATの取得
        self.pat = os.getenv('DEVOPS_PAT')
        if not self.pat:
            self.pat = self._get_pat_from_user()

        # 組織名の取得（user_config.jsonから既に読み込まれている）
        if not self.organization:
            print("user_config.jsonに組織名が設定されていません。")
            self.organization = self._get_organization_from_user()
            self._save_user_config()

        # 接続の検証
        validation_result = self._validate_connection()
        while not validation_result['success']:
            print("\n接続に失敗しました。")
            print(f"エラーの詳細: {validation_result['error']}")
            print("考えられる原因:")
            for cause in validation_result['possible_causes']:
                print(f"- {cause}")
            print("\n認証情報を再入力してください。")
            
            self.pat = self._get_pat_from_user()
            print(f"\n現在の組織名: {self.organization}")
            if input("組織名を変更しますか？(y/N): ").lower() == 'y':
                self.organization = self._get_organization_from_user()
                self._save_user_config()
            
            validation_result = self._validate_connection()

        # 検証成功後にヘッダーを設定
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

    def _validate_connection(self):
        """組織への接続を検証します。"""
        headers = self._create_headers()
        result = {
            'success': False,
            'error': '',
            'possible_causes': []
        }

        try:
            # Work Items APIを使用して接続を検証
            response = requests.get(
                f"https://dev.azure.com/{self.organization}/_apis/wit/wiql?api-version=7.0",
                headers=headers
            )

            if response.status_code == 200:
                result['success'] = True
                return result

            if response.status_code == 401:
                result['error'] = "認証エラー (401 Unauthorized)"
                result['possible_causes'] = [
                    "Personal Access Token (PAT)が無効または期限切れ",
                    "PATに必要な権限（Work Items - Read）が付与されていない",
                    "PATが正しく入力されていない"
                ]
            elif response.status_code == 403:
                result['error'] = "アクセス権限エラー (403 Forbidden)"
                result['possible_causes'] = [
                    "PATに組織へのアクセス権限がない",
                    "組織のセキュリティポリシーによりアクセスがブロックされている"
                ]
            elif response.status_code == 404:
                result['error'] = "組織が見つかりません (404 Not Found)"
                result['possible_causes'] = [
                    "組織名が間違っている",
                    "組織が存在しない",
                    "組織名の大文字小文字が異なる"
                ]
            else:
                result['error'] = f"APIエラー (Status Code: {response.status_code})"
                try:
                    error_detail = response.json().get('message', '')
                    if error_detail:
                        result['error'] += f" - {error_detail}"
                except:
                    pass
                result['possible_causes'] = [
                    "Azure DevOps APIに問題が発生している",
                    "ネットワーク接続に問題がある",
                    "組織の設定に問題がある"
                ]

        except requests.exceptions.ConnectionError:
            result['error'] = "接続エラー"
            result['possible_causes'] = [
                "インターネット接続が切断されている",
                "プロキシ設定が必要",
                "Azure DevOpsのサービスが利用できない"
            ]
        except requests.exceptions.RequestException as e:
            result['error'] = f"リクエストエラー: {str(e)}"
            result['possible_causes'] = [
                "ネットワーク接続に問題がある",
                "SSL/TLS証明書の問題がある",
                "タイムアウトが発生した"
            ]

        return result

    def _create_headers(self):
        """認証ヘッダーを生成します。"""
        auth_string = base64.b64encode(f":{self.pat}".encode('utf-8')).decode('utf-8')
        return {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        } 