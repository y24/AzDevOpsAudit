import os
import json
import logging
from datetime import datetime
from auth import DevOpsAuth
from config import ConfigManager
from workitem import WorkItemManager
from pullrequest import PullRequestManager

def setup_logging():
    """ロギングの設定を行います。"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def save_results(summary: dict, all_prs: list):
    """結果をファイルに保存します。"""
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # サマリーを保存
    summary_file = os.path.join(results_dir, f"summary_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # PRの詳細を保存
    pr_details_file = os.path.join(results_dir, f"pr_details_{timestamp}.json")
    with open(pr_details_file, 'w', encoding='utf-8') as f:
        json.dump(all_prs, f, indent=2, ensure_ascii=False)

def main():
    """メイン処理を実行します。"""
    # ロギングの設定
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 認証情報の取得
        auth = DevOpsAuth()
        headers = auth.get_auth_headers()
        organization = auth.get_organization()
        
        # 設定の読み込み
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # WorkItemManagerの初期化
        work_item_manager = WorkItemManager(organization, headers)
        
        # 処理対象のWorkItemを取得
        work_item_ids = work_item_manager.get_all_related_work_items(config)
        logger.info(f"処理対象のWorkItem数: {len(work_item_ids)}")
        
        # PullRequestManagerの初期化
        pr_manager = PullRequestManager(organization, headers)
        
        # 各WorkItemのPull Request情報を収集
        all_prs = []
        pr_info_list = []
        
        for work_item_id in work_item_ids:
            # WorkItemのプロジェクトを取得
            project, _ = work_item_manager.get_project_and_base_url(work_item_id)
            pr_ids = work_item_manager.get_pull_request_ids(work_item_id)
            
            for pr_id in pr_ids:
                pr_details = pr_manager.get_pull_request_details(project, pr_id)
                if pr_details:
                    pr_info = pr_manager.extract_pr_info(pr_details)
                    if pr_info:  # abandonedでない場合のみ追加
                        pr_info_list.append(pr_info)
                        all_prs.append({
                            'work_item_id': work_item_id,
                            'pull_request': pr_details
                        })
        
        # 情報をまとめる
        summary = pr_manager.summarize_pr_info(pr_info_list)
        
        # 結果を保存
        save_results(summary, all_prs)
        logger.info("処理が完了しました。")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 