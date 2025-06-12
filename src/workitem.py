import logging
from typing import List, Dict, Set, Tuple
import requests

class WorkItemManager:
    def __init__(self, organization: str, headers: Dict):
        self.organization = organization
        self.headers = headers
        self.logger = logging.getLogger(__name__)
        self.project_cache = {}

    def get_work_item_project(self, work_item_id: int) -> str:
        """WorkItemが属するプロジェクト名を取得します。"""
        try:
            url = f"https://dev.azure.com/{self.organization}/_apis/wit/workitems/{work_item_id}?$select=System.TeamProject&api-version=7.0"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()['fields']['System.TeamProject']
        except Exception as e:
            self.logger.error(f"WorkItem {work_item_id}のプロジェクト情報取得に失敗: {str(e)}")
            return None

    def get_project_and_base_url(self, work_item_id: int) -> Tuple[str, str]:
        """WorkItemのプロジェクトとベースURLを取得します。"""
        if work_item_id in self.project_cache:
            project = self.project_cache[work_item_id]
        else:
            project = self.get_work_item_project(work_item_id)
            if not project:
                raise ValueError(f"WorkItem {work_item_id}のプロジェクト情報を取得できませんでした。")
            self.project_cache[work_item_id] = project

        base_url = f"https://dev.azure.com/{self.organization}/{project}/_apis"
        return project, base_url

    def get_child_work_items(self, parent_ids: List[int]) -> Set[int]:
        """親WorkItemの子WorkItemのIDを取得します。"""
        child_ids = set()
        for parent_id in parent_ids:
            try:
                # プロジェクト情報を取得
                _, base_url = self.get_project_and_base_url(parent_id)
                
                # 関係を取得
                url = f"{base_url}/wit/workitems/{parent_id}?$expand=relations&api-version=7.0"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                relations = response.json().get('relations', [])
                for relation in relations:
                    if relation.get('rel') == 'System.LinkTypes.Hierarchy-Forward':
                        # URLから子WorkItemのIDを抽出
                        child_url = relation.get('url', '')
                        child_id = int(child_url.split('/')[-1])
                        child_ids.add(child_id)
            except Exception as e:
                self.logger.error(f"WorkItem {parent_id}の子WorkItem取得に失敗: {str(e)}")

        return child_ids

    def get_all_related_work_items(self, config: Dict) -> Set[int]:
        """設定に基づいて、すべての関連WorkItemのIDを取得します。"""
        all_work_items = set()
        
        # Featureの子WorkItemを取得
        feature_children = self.get_child_work_items(config['parent_feature_ids'])
        all_work_items.update(feature_children)
        
        # 設定ファイルで指定されたBacklog IDsを追加
        all_work_items.update(set(config['backlog_ids']))
        
        # これまでに集めたWorkItemの子WorkItemを取得
        current_items = list(all_work_items)
        child_items = self.get_child_work_items(current_items)
        all_work_items.update(child_items)
        
        # 親FeatureIDsも追加
        all_work_items.update(set(config['parent_feature_ids']))
        
        # 除外IDsを削除
        all_work_items = all_work_items - set(config['ignore_ids'])
        
        return all_work_items

    def get_work_item_details(self, work_item_id: int) -> Dict:
        """WorkItemの詳細情報を取得します。"""
        try:
            _, base_url = self.get_project_and_base_url(work_item_id)
            url = f"{base_url}/wit/workitems/{work_item_id}?$expand=relations&api-version=7.0"
            self.logger.info(f"WorkItem {work_item_id} の詳細情報を取得中: {url}")
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"API呼び出しエラー - Status: {response.status_code}, Response: {response.text}")
                return None
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"WorkItem {work_item_id}の詳細取得に失敗: {str(e)}")
            return None

    def get_pull_request_ids(self, work_item_id: int) -> List[int]:
        """WorkItemに関連付けられたPull RequestのIDを取得します。"""
        pr_ids = []
        self.logger.info(f"WorkItem {work_item_id} のPull Request情報を取得中...")
        
        work_item = self.get_work_item_details(work_item_id)
        if not work_item:
            self.logger.warning(f"WorkItem {work_item_id} の詳細情報を取得できませんでした")
            return pr_ids
            
        if 'relations' not in work_item:
            self.logger.info(f"WorkItem {work_item_id} には関連情報がありません")
            return pr_ids

        # 関連情報の詳細をログ出力
        self.logger.info(f"WorkItem {work_item_id} の関連情報:")
        for relation in work_item['relations']:
            self.logger.info(f"  関係タイプ: {relation.get('rel')}")
            self.logger.info(f"  URL: {relation.get('url')}")
            self.logger.info(f"  属性: {relation.get('attributes')}")

            # Pull Request関連の情報を探す
            # attributes.nameが"Pull Request"の場合
            if relation.get('attributes', {}).get('name') == 'Pull Request':
                url = relation.get('url', '')
                try:
                    # URLからPR IDを抽出
                    pr_id = int(url.split('/')[-1])
                    self.logger.info(f"  PR検出: {pr_id}")
                    if pr_id not in pr_ids:
                        pr_ids.append(pr_id)
                except (ValueError, IndexError):
                    self.logger.warning(f"  PRのURL {url} からIDを抽出できませんでした")

        if not pr_ids:
            self.logger.info(f"WorkItem {work_item_id} に関連するPRは見つかりませんでした")
        else:
            self.logger.info(f"WorkItem {work_item_id} に関連するPR: {pr_ids}")

        return pr_ids 