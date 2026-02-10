from __future__ import annotations

import argparse
from pathlib import Path

from dongdong_bot.agent.allowlist_store import AllowlistStore
from dongdong_bot.agent.memory import MemoryStore
from dongdong_bot.config import ALLOWLIST_FILENAME, EMBEDDING_INDEX_FILENAME


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="記憶管理工具")
    parser.add_argument("action", choices=["delete", "reset"], help="delete 或 reset")
    parser.add_argument("--scope", choices=["all", "range", "keyword"], default="all")
    parser.add_argument("--start", help="開始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="結束日期 YYYY-MM-DD")
    parser.add_argument("--keyword", help="關鍵字")
    parser.add_argument("--user-id", required=True, help="操作人 user_id")
    parser.add_argument("--channel", default="telegram", help="channel 類型")
    return parser.parse_args()


def _ensure_allowed(root: Path, user_id: str, channel: str) -> bool:
    allowlist_path = root / "data" / ALLOWLIST_FILENAME
    store = AllowlistStore(str(allowlist_path))
    return store.is_allowed(user_id, channel)


def main() -> int:
    args = _parse_args()
    root = _project_root()
    if not _ensure_allowed(root, args.user_id, args.channel):
        print("權限不足：不在允許名單內。")
        return 1

    memory_dir = root / "data"
    embedding_path = memory_dir / EMBEDDING_INDEX_FILENAME
    store = MemoryStore(str(memory_dir), embedding_index_path=str(embedding_path))

    if args.action == "reset":
        removed = store.delete_all()
        print(f"已重置記憶，共移除 {removed} 筆。")
        return 0

    if args.scope == "all":
        removed = store.delete_all()
        print(f"已刪除記憶，共移除 {removed} 筆。")
        return 0

    if args.scope == "range":
        if not args.start or not args.end:
            print("請提供 --start 與 --end")
            return 2
        removed = store.delete_by_date_range(args.start, args.end)
        print(f"已刪除日期區間記憶，共移除 {removed} 筆。")
        return 0

    if args.scope == "keyword":
        if not args.keyword:
            print("請提供 --keyword")
            return 2
        removed = store.delete_by_keyword(args.keyword, args.start, args.end)
        print(f"已刪除關鍵字記憶，共移除 {removed} 筆。")
        return 0

    print("未知操作")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
