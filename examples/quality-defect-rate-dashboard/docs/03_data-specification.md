# データ仕様

## 注意

以下は仮置きです。現行Excelと生データの解析後に確定してください。

## 想定カラム

| 元カラム | アプリ内名称 | 意味 | 型 | 状態 |
|---|---|---|---|---|
| supplier_id | supplier_id | 取引先ID | 文字列 | 要確認 |
| supplier_name | supplier_name | 取引先名 | 文字列 | 要確認 |
| inspection_date | inspection_date | 検品日 | 日付 | 要確認 |
| defect_qty | defect_quantity | 不良数量 | 数値 | 要確認 |
| inspected_qty | inspected_quantity | 検品数量 | 数値 | 要確認 |

## 想定計算

```text
月別不良率 = 月別不良数量合計 ÷ 月別検品数量合計
```

この計算式は業務担当者の確認が必要です。
