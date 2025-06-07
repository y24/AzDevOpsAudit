import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class CommitDiffManager:
    def __init__(self, organization: str, headers: Dict[str, str]):
        self.organization = organization
        self.headers = headers

    def get_commit_diff_stats_classified(
        self,
        project: str,
        repository: str,
        base_commit: str,
        target_commit: str,
        exclude_dirs: List[str] = None
    ) -> Dict[str, Any]:
        """
        指定された2つのコミット間の差分を取得し、統計情報を返します。

        Args:
            project (str): プロジェクト名
            repository (str): リポジトリ名
            base_commit (str): 基準となるコミットハッシュ
            target_commit (str): 比較対象のコミットハッシュ
            exclude_dirs (List[str], optional): 除外するディレクトリのリスト

        Returns:
            Dict[str, Any]: 差分の統計情報
        """
        if exclude_dirs is None:
            exclude_dirs = []

        base_url = f"https://dev.azure.com/{self.organization}/{project}/_apis/git/repositories/{repository}"

        # コミット差分取得
        diff_url = (
            f"{base_url}/diffs/commits"
            f"?baseVersion={base_commit}&targetVersion={target_commit}"
            f"&$top=1000&api-version=7.1-preview.1"
        )
        response = requests.get(diff_url, headers=self.headers)
        response.raise_for_status()
        diff_data = response.json()

        file_paths = [change["item"]["path"] for change in diff_data.get("changes", [])]

        count_added = 0
        count_deleted = 0
        count_modified = 0
        file_diffs = []

        for path in file_paths:
            # 除外ディレクトリにマッチする場合はスキップ
            if any(path.startswith(ex_dir.rstrip('/') + '/') for ex_dir in exclude_dirs):
                continue

            encoded_path = quote(path, safe='')
            content_diff_url = (
                f"{base_url}/diffs/contents"
                f"?baseVersion={base_commit}&targetVersion={target_commit}&path={encoded_path}"
                f"&api-version=7.1-preview.1"
            )
            r = requests.get(content_diff_url, headers=self.headers)
            if r.status_code == 200:
                diff = r.json()
                add = diff.get("addLineCount", 0)
                delete = diff.get("deleteLineCount", 0)

                # 分類ロジック
                if add > 0 and delete > 0:
                    kind = "modified"
                    count_modified += add + delete
                elif add > 0:
                    kind = "added"
                    count_added += add
                elif delete > 0:
                    kind = "deleted"
                    count_deleted += delete
                else:
                    kind = "unchanged"

                file_diffs.append({
                    "path": path,
                    "added": add,
                    "deleted": delete,
                    "type": kind
                })
            else:
                logger.warning(f"⚠️ Skipped {path}: {r.status_code} - {r.text}")

        return {
            "added": count_added,
            "deleted": count_deleted,
            "modified": count_modified,
            "files": file_diffs
        }

    def get_repository_info(self, project: str) -> List[Dict[str, Any]]:
        """
        プロジェクト内の全リポジトリ情報を取得します。

        Args:
            project (str): プロジェクト名

        Returns:
            List[Dict[str, Any]]: リポジトリ情報のリスト
        """
        url = f"https://dev.azure.com/{self.organization}/{project}/_apis/git/repositories?api-version=7.1-preview.1"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["value"] 