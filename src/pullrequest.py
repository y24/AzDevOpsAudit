import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests

class PullRequestManager:
    def __init__(self, organization: str, headers: Dict):
        self.organization = organization
        self.headers = headers
        self.logger = logging.getLogger(__name__)

    def get_pull_request_details(self, project: str, pr_id: int) -> Optional[Dict]:
        """Pull Requestの詳細情報を取得します。"""
        try:
            url = f"https://dev.azure.com/{self.organization}/{project}/_apis/git/pullrequests/{pr_id}?api-version=7.0"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"PR {pr_id}の詳細取得に失敗: {str(e)}")
            return None

    def extract_pr_info(self, pr_details: Dict) -> Dict:
        """Pull Requestから必要な情報を抽出します。"""
        if not pr_details:
            return None

        # abandonedの場合はNoneを返す
        if pr_details.get('status') == 'abandoned':
            return None

        return {
            'repository': pr_details.get('repository', {}).get('name'),
            'target_branch': pr_details.get('targetRefName', '').replace('refs/heads/', ''),
            'created_date': pr_details.get('creationDate'),
            'commit_id': pr_details.get('lastMergeSourceCommit', {}).get('commitId'),
            'reviewers': [
                reviewer.get('displayName')
                for reviewer in pr_details.get('reviewers', [])
            ],
            'status': pr_details.get('status'),
            'title': pr_details.get('title'),
            'url': pr_details.get('url')
        }

    def summarize_pr_info(self, pr_info_list: List[Dict]) -> Dict:
        """Pull Request情報をまとめます。"""
        summary = {}
        
        for pr_info in pr_info_list:
            if not pr_info:
                continue

            repo = pr_info['repository']
            if repo not in summary:
                summary[repo] = {
                    'branches': {},
                    'reviewers': set()
                }

            branch = pr_info['target_branch']
            if branch not in summary[repo]['branches']:
                summary[repo]['branches'][branch] = {
                    'oldest_commit': {'date': None, 'hash': None},
                    'newest_commit': {'date': None, 'hash': None}
                }

            # レビュワーを追加
            summary[repo]['reviewers'].update(pr_info['reviewers'])

            # コミット日時を処理
            created_date = datetime.strptime(pr_info['created_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            branch_info = summary[repo]['branches'][branch]

            if (not branch_info['oldest_commit']['date'] or 
                created_date < datetime.strptime(branch_info['oldest_commit']['date'], "%Y-%m-%dT%H:%M:%S.%fZ")):
                branch_info['oldest_commit'] = {
                    'date': pr_info['created_date'],
                    'hash': pr_info['commit_id']
                }

            if (not branch_info['newest_commit']['date'] or 
                created_date > datetime.strptime(branch_info['newest_commit']['date'], "%Y-%m-%dT%H:%M:%S.%fZ")):
                branch_info['newest_commit'] = {
                    'date': pr_info['created_date'],
                    'hash': pr_info['commit_id']
                }

        # setをリストに変換
        for repo in summary:
            summary[repo]['reviewers'] = list(summary[repo]['reviewers'])

        return summary 