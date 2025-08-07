# 🤖 東吳大學課程餘額查詢機器人

一個基於 LINE Bot 的東吳大學課程餘額查詢與監控系統，能夠自動監控課程名額並在有空位時即時通知。

## ✨ 功能特色

- 🔍 **即時課程查詢**：輸入4位數課程編號即可查詢課程詳細資訊
- 🎯 **自動監控系統**：無名額課程自動開始監控，有名額時立即通知
- 📋 **監控清單管理**：查看、取消單一或全部監控課程
- ⚡ **即時通知**：透過 LINE 推播第一時間通知課程餘額
- 🛡️ **使用限制**：每位使用者最多可監控10門課程

## 🚀 快速開始

### 前置需求

- Python 3.7+
- LINE Bot Channel (Channel Access Token & Channel Secret)
- 東吳大學學生帳號

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd course-monitoring-bot
```

2. **安裝相依套件**
```bash
pip install -r requirements.txt
```

3. **環境變數設定**

創建 `.env` 文件並設定以下變數：
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
SOOCHOW_USERNAME=your_soochow_username
SOOCHOW_PASSWORD=your_soochow_password
```

4. **啟動服務**
```bash
python main.py
```

服務將在 `http://0.0.0.0:5000` 上運行。

## 📱 使用方式

### LINE Bot 指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `課程編號` | 查詢課程餘額並自動監控 | `7002` |
| `清單` | 查看目前監控的課程清單 | `清單` |
| `取消 課程編號` | 取消監控特定課程 | `取消 7002` |
| `取消 全部` | 取消所有監控課程 | `取消 全部` |
| `幫助` | 顯示使用說明 | `幫助` |

### 使用流程

1. **查詢課程**：直接輸入4位數課程編號
2. **自動監控**：如果課程沒有餘額，系統會自動開始監控
3. **即時通知**：當課程有餘額時，會立即透過 LINE 通知
4. **管理監控**：透過清單查看或取消不需要的監控

## 🏗️ 系統架構

### 核心組件

- **CourseQuery 類別**：負責東吳大學系統的登入與課程查詢
- **監控系統**：使用多線程背景監控課程狀態
- **LINE Bot 整合**：處理用戶訊息與推播通知
- **Flask Web 服務**：提供 webhook 端點與狀態頁面

### 技術棧

- **後端框架**：Flask
- **爬蟲技術**：requests + BeautifulSoup
- **訊息平台**：LINE Bot SDK
- **並發處理**：Python threading
- **資料解析**：正則表達式 + HTML 解析

## 🔧 設定說明

### 環境變數

| 變數名稱 | 說明 | 必需 |
|----------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 頻道存取權杖 | ✅ |
| `LINE_CHANNEL_SECRET` | LINE Bot 頻道密鑰 | ✅ |
| `SOOCHOW_USERNAME` | 東吳大學學號 | ✅ |
| `SOOCHOW_PASSWORD` | 東吳大學密碼 | ✅ |

### 系統參數

```python
MONITOR_INTERVAL = 5              # 監控間隔(秒)
MAX_MONITORING_PER_USER = 10      # 每用戶最大監控課程數
REQUEST_TIMEOUT = 30              # 請求超時時間(秒)
```

## 📊 監控機制

### 監控邏輯

1. **課程查詢**：每5秒檢查一次課程狀態
2. **餘額檢測**：比較目前修課人數與課程上限
3. **通知觸發**：發現有餘額時立即推送 LINE 訊息
4. **自動停止**：通知後自動移除該課程的監控

### 資料結構

```python
monitoring_data = {
    user_id: {
        course_id: {
            'course_name': str,
            'thread': Thread
        }
    }
}
```

## 🚀 部署說明

### 本地開發
```bash
python main.py
```

### 生產環境

建議使用 gunicorn 或其他 WSGI 服務器：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Docker 部署 (可選)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

## 🛠️ 故障排除

### 常見問題

1. **登入失敗**
   - 檢查東吳大學帳號密碼是否正確
   - 確認學校系統是否正常運作

2. **LINE Bot 無回應**
   - 驗證 Channel Access Token 和 Channel Secret
   - 檢查 webhook URL 設定

3. **課程查詢失敗**
   - 確認課程編號格式正確（4位數字）
   - 檢查學校選課系統是否開放

### 日誌檢查

系統會輸出詳細的執行日誌，包括：
- 登入狀態
- 課程查詢結果
- 監控狀態變化
- 錯誤訊息

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 此專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 授權

此專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

## ⚠️ 免責聲明

此機器人僅供學習和個人使用，請遵守東吳大學相關規定。使用者需自行承擔使用風險。

---

## 📞 支援與回饋

如有問題或建議，歡迎透過 GitHub Issues 聯繫我們。