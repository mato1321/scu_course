# 🤖 東吳大學課程餘額查詢機器人

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.17.1-00C300.svg)](https://github.com/line/line-bot-sdk-python)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一個為**東吳大學**學生設計的強大 **LINE Bot** 應用程式，能夠即時監控課程餘額狀況。系統會自動追蹤課程選課狀態，並在有名額時立即發送通知訊息。

**繁體中文** | [English](README.md)

## ✨ 核心功能

- 🔍 **即時課程查詢**：使用4位數課程編號快速查詢課程詳細資訊
- 🎯 **智慧型自動監控**：自動監控無名額課程，有空位時立即通知
- 📋 **完整管理介面**：查看、新增、移除監控清單中的課程
- ⚡ **即時推播通知**：透過 LINE 訊息在第一時間收到餘額通知
- 🛡️ **資源管理**：限制每位使用者最多監控10門課程，並使用執行緒安全機制
- 🔄 **容錯處理**：自動重試機制與錯誤恢復功能

## 🏗️ 系統架構

### 核心元件

- **CourseQuery 類別**：處理東吳大學系統驗證與課程資料擷取
- **監控引擎**：多執行緒背景監控，每5秒檢查一次課程狀況
- **LINE Bot 整合**：Webhook 處理與推播通知傳送
- **Flask Web 服務**：RESTful API 端點與健康監控儀表板

### 技術堆疊

- **後端框架**：Flask 3.1.1
- **網頁爬蟲**：requests 2.32.4 + BeautifulSoup 4.13.4
- **訊息平台**：LINE Bot SDK 3.17.1
- **並發處理**：Python threading 配合執行緒安全鎖
- **資料解析**：正規表示式 + DOM 解析
- **環境管理**：python-dotenv 1.0.0

## 🚀 快速入門

### 前置需求

- **Python 3.7+** 並安裝 pip 套件管理器
- **LINE Bot 頻道** (Channel Access Token 與 Channel Secret)
- **東吳大學帳號** (學生認證資料)
- **ngrok** 用於本地開發隧道

### 安裝指南

1. **複製儲存庫**
```bash
git clone https://github.com/yourusername/soochow-course-bot.git
cd soochow-course-bot
```

2. **建立虛擬環境 (建議)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

3. **安裝相依性套件**
```bash
pip install -r requirements.txt
```

4. **環境變數設定**

在專案根目錄建立 `.env` 檔案：
```env
LINE_CHANNEL_ACCESS_TOKEN=你的_line_channel_access_token
LINE_CHANNEL_SECRET=你的_line_channel_secret
SOOCHOW_USERNAME=你的_東吳大學學號
SOOCHOW_PASSWORD=你的_東吳大學密碼
```

5. **啟動應用程式**
```bash
python main.py
```

服務將在 `http://localhost:5000` 上運行

## 🌐 ngrok 設定與整合

### 安裝 ngrok

1. **下載 ngrok**
   - 前往 [ngrok.com](https://ngrok.com/) 並建立免費帳號
   - 下載適用於您作業系統的版本

2. **認證設定**
```bash
ngrok authtoken 您的_認證_TOKEN
```

### 隧道設定

1. **啟動您的 Flask 應用程式**
```bash
python main.py
```

2. **建立 HTTP 隧道 (開新終端機)**
```bash
ngrok http 5000
```

3. **複製 HTTPS 網址**
```
ngrok by @inconshreveable

Session Status    online
Account           your_account (Plan: Free)
Version           2.3.40
Region            United States (us)
Web Interface     http://127.0.0.1:4040
Forwarding        http://abc123.ngrok.io -> http://localhost:5000
Forwarding        https://abc123.ngrok.io -> http://localhost:5000  <-- 使用此網址
```

### LINE Bot Webhook 設定

1. **前往 LINE Developers Console**
   - 到 [developers.line.biz](https://developers.line.biz/)
   - 選擇您的頻道

2. **更新 Webhook 網址**
   - 導覽至 **Messaging API** 分頁
   - 設定 **Webhook URL**：`https://abc123.ngrok.io/callback`
   - 啟用 **Use webhook**
   - 點擊 **Verify** 測試連線

3. **測試您的機器人**
   - 使用 QR code 加入機器人為好友
   - 發送測試訊息

### 正式環境部署

正式環境建議考慮：
- **付費 ngrok 方案** (每月 $8) 獲得穩定網址
- **雲端主機**：Railway、Render 或 DigitalOcean
- **網域與 SSL**：自訂網域配合 HTTPS 憑證

## 📱 機器人指令與使用方式

### 可用指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `[4位數編號]` | 查詢課程並在無名額時自動監控 | `7002` |
| `清單` | 查看目前監控清單 | `清單` |
| `取消 [課程編號]` | 取消監控特定課程 | `取消 7002` |
| `取消 全部` | 取消所有監控 | `取消 全部` |
| `幫助` | 顯示使用說明 | `幫助` |

### 工作流程

1. **課程查詢**：發送4位數課程編號給機器人
2. **自動監控**：系統自動監控無餘額的課程
3. **即時通知**：有餘額時透過 LINE 收到通知
4. **自動清理**：成功通知後自動停止監控

### 回應範例

**有餘額：**
```
課程名稱：資料結構
選課編號：7002
科目代碼：CSIE2001
學分數：3
修課人數：45/60
剩餘名額：15 人
(目前有15個名額，請盡快去加選!)
```

**無餘額（自動監控啟動）：**
```
成功加入監控清單!
課程名稱：資料結構
選課編號：7002
科目代碼：CSIE2001
學分數：3
修課人數：60/60
剩餘名額：0 人
(目前沒有名額，當有名額時會由line主動通知)
```

## 🔧 設定參數

### 環境變數

| 變數名稱 | 說明 | 必需 |
|----------|------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot 頻道存取權杖 | ✅ |
| `LINE_CHANNEL_SECRET` | LINE Bot 頻道密鑰 | ✅ |
| `SOOCHOW_USERNAME` | 東吳大學學號 | ✅ |
| `SOOCHOW_PASSWORD` | 東吳大學密碼 | ✅ |

### 系統參數

```python
MONITOR_INTERVAL = 5              # 監控間隔（秒）
MAX_MONITORING_PER_USER = 10      # 每用戶最大監控課程數
REQUEST_TIMEOUT = 30              # HTTP 請求超時時間
PORT = 5000                       # Flask 伺服器埠號
```

## 📊 監控機制

### 演算法

1. **查詢循環**：每5秒檢查課程狀態
2. **餘額偵測**：比較目前修課人數與課程容量
3. **通知觸發**：發現有餘額時發送 LINE 推播訊息
4. **自動終止**：通知發送後自動移除課程監控

### 資料結構

```python
monitoring_data = {
    user_id: {
        course_id: {
            'course_name': str,
            'thread': threading.Thread
        }
    }
}
```

### 執行緒安全

- **監控鎖定**：`threading.Lock()` 保護並發存取
- **Daemon 執行緒**：背景監控執行緒隨主程序自動終止
- **資源清理**：取消監控時自動終止執行緒

## 🚀 部署選項

### 本地開發
```bash
python main.py
```

### 使用 Gunicorn 的正式環境
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Docker 部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
```

建置與執行：
```bash
docker build -t soochow-course-bot .
docker run -p 5000:5000 --env-file .env soochow-course-bot
```

### 雲端平台

**Railway.app**
1. 連接 GitHub 儲存庫
2. 新增環境變數
3. 自動部署

**Render.com**
1. 建立新的 Web 服務
2. 連接儲存庫
3. 設定建置指令：`pip install -r requirements.txt`
4. 設定啟動指令：`python main.py`

## 🔍 故障排除

### 常見問題

**登入失敗**
- 驗證東吳大學認證資料
- 檢查大學系統是否可存取
- 確保遠端存取時有 VPN 連線

**LINE Bot 無回應**
- 驗證 Channel Access Token 和 Secret
- 確認 webhook URL 設定
- 檢查 ngrok 隧道狀態
- 查看 Flask 應用程式日誌

**課程查詢錯誤**
- 確認4位數課程編號格式
- 驗證課程在本學期是否存在
- 檢查課程選課是否開放

**監控功能無效**
- 確保 LINE Developers 帳號已綁定信用卡
- 檢查 Push Message API 配額
- 在日誌中驗證執行緒執行狀況

### 除錯

**啟用除錯模式**
```python
DEBUG_MODE = True
app.run(host='0.0.0.0', port=5000, debug=True)
```

**日誌分析**
系統輸出詳細的執行日誌：
- 認證狀態
- 課程查詢結果
- 監控狀態變化
- 錯誤訊息與堆疊追蹤

## 🧪 測試

### 單元測試
```bash
# 安裝測試相依性
pip install pytest pytest-flask

# 執行測試
pytest tests/
```

### 手動測試
1. **健康檢查**：造訪 `http://localhost:5000`
2. **課程查詢**：發送課程編號給 LINE 機器人
3. **監控**：驗證背景執行緒執行
4. **通知**：測試推播訊息傳送

## 📈 效能與擴展性

### 監控容量
- **每位使用者**：最多10個並發課程監控
- **系統**：理論上限取決於伺服器資源
- **執行緒**：每位使用者每門課程一個監控執行緒

### 最佳化技術
- **會話重用**：持續的 HTTP 會話用於認證
- **執行緒池**：考慮為高使用者量實作執行緒池
- **資料庫整合**：將監控資料儲存在持久性儲存中以提高擴展性
- **快取機制**：實作課程資料快取以減少伺服器負載

## 🤝 貢獻

我們歡迎貢獻！請遵循以下指南：

### 開發設定
```bash
git clone https://github.com/yourusername/soochow-course-bot.git
cd soochow-course-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 貢獻流程
1. **Fork** 儲存庫
2. **建立** 功能分支 (`git checkout -b feature/amazing-feature`)
3. **提交** 變更 (`git commit -m 'Add amazing feature'`)
4. **推送** 至分支 (`git push origin feature/amazing-feature`)
5. **開啟** Pull Request

### 程式碼標準
- 遵循 PEP 8 風格指南
- 為函數和類別新增文件字串
- 為新功能包含單元測試
- 適時更新文件

## 📄 授權

此專案採用 **MIT 授權** - 詳見 [LICENSE](LICENSE) 檔案

## ⚠️ 免責聲明

此機器人僅供**教育和個人使用**。使用者必須遵守東吳大學的服務條款和相關規定。開發者對任何誤用或違規行為不承擔責任。

**重要提醒：**
- 尊重大學的課程選課系統
- 避免過度請求對伺服器造成負載
- 在選課高峰期間負責任地使用
- 確保符合學術誠信政策

## 📞 支援與回饋

- **問題回報**：[GitHub Issues](https://github.com/yourusername/soochow-course-bot/issues)
- **討論區**：[GitHub Discussions](https://github.com/yourusername/soochow-course-bot/discussions)
- **電子信箱**：your.email@example.com

## 🙏 致謝

- **東吳大學** 提供課程系統
- **LINE Corporation** 提供訊息平台
- **貢獻者** 協助改善此專案
- **開源社群** 提供優秀的函式庫

---

用 ❤️ 為東吳大學學生製作