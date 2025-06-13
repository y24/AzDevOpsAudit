import os
import json
import inquirer
from typing import List, Dict, Optional

class ConfigManager:
    def __init__(self):
        self.config_dir = "configs"
        os.makedirs(self.config_dir, exist_ok=True)

    def list_config_files(self) -> List[str]:
        """利用可能な設定ファイルの一覧を取得します。"""
        return [f for f in os.listdir(self.config_dir) if f.endswith('.json')]

    def select_config_file(self) -> str:
        """ユーザーに設定ファイルを選択させます。"""
        config_files = self.list_config_files()
        if not config_files:
            raise FileNotFoundError("設定ファイルが見つかりません。configsディレクトリにJSONファイルを配置してください。")

        questions = [
            inquirer.List('config_file',
                         message='使用する設定ファイルを選択してください',
                         choices=config_files,
                         carousel=True)  # 最後の項目から最初の項目に循環できるようにする
        ]

        answers = inquirer.prompt(questions)
        return answers['config_file']

    def load_config(self, config_file: Optional[str] = None) -> Dict:
        """設定ファイルを読み込みます。"""
        if config_file is None:
            config_file = self.select_config_file()

        config_path = os.path.join(self.config_dir, config_file)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 必要なフィールドの存在確認と型変換
            config['parent_feature_ids'] = self._parse_id_list(config.get('parent_feature_ids', ''))
            config['backlog_item_ids'] = self._parse_id_list(config.get('backlog_item_ids', ''))
            config['ignore_ids'] = self._parse_id_list(config.get('ignore_ids', ''))
            config['is_only_completed_item'] = bool(config.get('is_only_completed_item', False))

            return config
        except Exception as e:
            raise ValueError(f"設定ファイルの読み込みに失敗しました: {str(e)}")

    def _parse_id_list(self, id_input: any) -> List[int]:
        """ID文字列またはリストをintのリストに変換します。"""
        if not id_input:
            return []
        
        # 既にリストの場合
        if isinstance(id_input, list):
            return [int(id) for id in id_input if str(id).strip()]
        
        # 文字列の場合
        if isinstance(id_input, str):
            return [int(id.strip()) for id in id_input.split(',') if id.strip()]
        
        # 数値の場合（単一のID）
        if isinstance(id_input, (int, float)):
            return [int(id_input)]
        
        raise ValueError(f"サポートされていないID形式です: {type(id_input)}") 