"""Inventory lookup and LINE-friendly response formatting."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InventoryItem:
    code: str
    name: str
    quantity: str
    unit: str
    recent_purchase_price: str

    @property
    def in_stock(self) -> bool:
        try:
            return float(self.quantity) > 0
        except ValueError:
            return False


class InventoryService:
    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path

    def all_items(self) -> list[InventoryItem]:
        with self.csv_path.open(encoding="utf-8-sig", newline="") as source:
            return [
                InventoryItem(
                    code=row["code"].strip(),
                    name=row["name"].strip(),
                    quantity=row["quantity"].strip(),
                    unit=row["unit"].strip(),
                    recent_purchase_price=row.get("recent_purchase_price", "").strip(),
                )
                for row in csv.DictReader(source)
            ]

    def search(self, query: str) -> list[InventoryItem]:
        needle = _normalise(query)
        if not needle:
            return []

        return [
            item
            for item in self.all_items()
            if needle in _normalise(item.code) or needle in _normalise(item.name)
        ]


def _normalise(value: str) -> str:
    return "".join(value.casefold().split()).replace("（", "(").replace("）", ")")


def build_inventory_reply(query: str, inventory: InventoryService) -> str:
    cleaned_query = query.strip()
    if not cleaned_query or _normalise(cleaned_query) in {"help", "幫助", "說明"}:
        return (
            "您好，這裡是真廣海鮮食材行 👋\n\n"
            "請直接輸入商品名稱或商品編號查詢庫存，例如：\n"
            "白蝦\nB005\n\n"
            "輸入「庫存」可查看全部品項。"
        )

    if _normalise(cleaned_query) in {"庫存", "全部庫存", "所有庫存"}:
        items = inventory.all_items()
        if not items:
            return "目前沒有庫存資料。"
        return "📦 目前庫存\n\n" + "\n\n".join(_format_summary(item) for item in items)

    matches = inventory.search(cleaned_query)
    if not matches:
        return (
            f"查不到「{cleaned_query}」的庫存資料。\n"
            "請確認商品名稱或商品編號；也可以輸入「幫助」。"
        )

    if len(matches) == 1:
        item = matches[0]
        status = "有貨" if item.in_stock else "缺貨"
        return (
            f"📦 {item.code}｜{item.name}\n"
            f"目前庫存：{item.quantity} {item.unit}\n"
            f"最近進價：{item.recent_purchase_price or '尚未匯入'}\n"
            f"庫存狀態：{status}"
        )

    result = f"📦「{cleaned_query}」查到 {len(matches)} 個品項\n\n"
    result += "\n\n".join(_format_summary(item) for item in matches)
    return result


def _format_summary(item: InventoryItem) -> str:
    status = "有貨" if item.in_stock else "缺貨"
    price = item.recent_purchase_price or "尚未匯入"
    return (
        f"{item.code}｜{item.name}\n"
        f"庫存：{item.quantity} {item.unit}｜{status}\n"
        f"最近進價：{price}"
    )
