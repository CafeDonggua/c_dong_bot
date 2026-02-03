from __future__ import annotations

from dongdong_bot.lib.report_content import normalize_report_content
from dongdong_bot.lib.search_schema import SearchResponse


class SearchFormatter:
    @staticmethod
    def format(response: SearchResponse) -> str:
        if response.is_empty():
            return (
                "找不到相關結果，請嘗試：\n"
                "1) 縮小範圍（加入時間/地點/公司名稱）\n"
                "2) 改用同義詞或別名\n"
                "3) 分拆成 2~3 個較小主題再查"
            )
        if not response.summary and response.raw_text:
            return response.raw_text
        normalized = normalize_report_content(
            response,
            reason="內容不足或來源缺失",
            suggestion="請補充關鍵字或改用 /summary 指令取得更多內容。",
        )
        summary = normalized.summary
        bullets = normalized.bullets
        sources = normalized.sources
        bullets_block = "\n".join(f"- {item}" for item in bullets)
        sources_block = "\n".join(f"- {item}" for item in sources)
        return (
            "摘要：\n"
            f"{summary}\n\n"
            "重點：\n"
            f"{bullets_block}\n\n"
            "來源：\n"
            f"{sources_block}"
        )

    @staticmethod
    def format_error(reason: str, suggestion: str) -> str:
        return f"搜尋失敗：{reason}\n建議：{suggestion}"
