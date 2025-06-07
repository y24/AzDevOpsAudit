import logging
from typing import List, Dict, Set
import requests

class WorkItemManager:
    def __init__(self, organization: str, project: str, headers: Dict):
        self.organization = organization
        self.project = project
        self.headers = headers
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        self.logger = logging.getLogger(__name__)

    def get_child_work_items(self, parent_ids: List[int]) -> Set[int]:
        """親WorkItemの子WorkItemのIDを取得します。"""
        child_ids = set()
        for parent_id in parent_ids:
            try:
                # 関係を取得
                url = f"{self.base_url}/wit/workitems/{parent_id}?$expand=relations&api-version=7.0"
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
        child_items = self.get_child_work_items(list(all_work_items))
        all_work_items.update(child_items)
        
        # 親FeatureIDsも追加
        all_work_items.update(set(config['parent_feature_ids']))
        
        # 除外IDsを削除
        all_work_items = all_work_items - set(config['ignore_ids'])
        
        return all_work_items

    def get_work_item_details(self, work_item_id: int) -> Dict:
        """WorkItemの詳細情報を取得します。"""
        try:
            url = f"{self.base_url}/wit/workitems/{work_item_id}?$expand=relations&api-version=7.0"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"WorkItem {work_item_id}の詳細取得に失敗: {str(e)}")
            return None

    def get_pull_request_ids(self, work_item_id: int) -> List[int]:
        """WorkItemに関連付けられたPull RequestのIDを取得します。"""
        pr_ids = []
        work_item = self.get_work_item_details(work_item_id)
        
        if not work_item or 'relations' not in work_item:
            return pr_ids

        for relation in work_item['relations']:
            if relation.get('rel') == 'ArtifactLink' and 'pullRequestId' in relation.get('attributes', {}):
                pr_id = relation['attributes']['pullRequestId']
                pr_ids.append(pr_id)

        return pr_ids 