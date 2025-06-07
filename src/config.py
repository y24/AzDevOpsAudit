import os
import json
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

        print("\n利用可能な設定ファイル:")
        for i, file in enumerate(config_files, 1):
            print(f"{i}. {file}")

        while True:
            try:
                selection = int(input("\n使用する設定ファイルの番号を入力してください: "))
                if 1 <= selection <= len(config_files):
                    return config_files[selection - 1]
                print("無効な選択です。")
            except ValueError:
                print("数字を入力してください。")

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
            config['backlog_ids'] = self._parse_id_list(config.get('backlog_ids', ''))
            config['ignore_ids'] = self._parse_id_list(config.get('ignore_ids', ''))
            config['is_only_completed_item'] = bool(config.get('is_only_completed_item', False))

            return config
        except Exception as e:
            raise ValueError(f"設定ファイルの読み込みに失敗しました: {str(e)}")

    def _parse_id_list(self, id_string: str) -> List[int]:
        """カンマ区切りのID文字列をリストに変換します。"""
        if not id_string:
            return []
        return [int(id.strip()) for id in str(id_string).split(',') if id.strip()] 