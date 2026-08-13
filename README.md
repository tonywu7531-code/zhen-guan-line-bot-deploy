# 真廣海鮮 LINE Bot（庫存查詢）

客戶在 LINE 官方帳號傳送商品名稱、商品編號或「庫存」，Bot 就會回覆庫存資料。

## 第一版功能

- 查商品名稱：`白蝦`
- 查商品編號：`B005`
- 查全部庫存：`庫存`
- 查不到時提供清楚提示

第一版的庫存資料保存在 [`data/inventory.csv`](data/inventory.csv)。可直接在 GitHub 編輯這個檔案更新庫存；未來可把資料來源替換為鈞陽 ERP，而 LINE Bot 的操作方式不變。

## 本機啟動

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

開啟 `http://127.0.0.1:8000/health`，應會看到：

```json
{"status":"ok"}
```

## LINE 憑證

在 `.env` 或部署平台的環境變數設定下列值：

```text
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
```

切勿把 `.env` 或 LINE Token 上傳到 GitHub。專案的 `.gitignore` 已排除它們。

## 部署設定

- Build Command：`pip install -r requirements.txt`
- Start Command：`uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path：`/health`
- LINE Webhook URL：`https://你的網域/webhook`

## 更新庫存

在 `data/inventory.csv` 中每一列依序填入：

```csv
code,name,quantity,unit
B005,20/30 白蝦（有氧）,15,箱
```

更新 CSV 後重新部署即可讓 Bot 使用新的資料。第一版不會自動同步 ERP；後續可改為由 ERP 的 API 或匯出檔定期更新資料來源。
