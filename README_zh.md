# 選修戰士🦸 (東吳大學課程餘額查詢機器人)

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.17.1-00C300.svg)](https://github.com/line/line-bot-sdk-python)

這是一個東吳大學學生專屬的linebot應用程式，能夠即時監控課程餘額狀況。系統會自動追蹤課程選課狀態，並在有名額時立即發送通知訊息。

**繁體中文** | [English](README.md)

## 核心功能

-  **即時課程查詢**：使用4位數課程編號快速查詢課程詳細資訊
-  **智慧型自動監控**：自動監控無名額課程，有空位時立即通知
-  **完整管理介面**：查看、新增、移除監控清單中的課程
-  **即時推播通知**：透過 LINE 訊息在第一時間收到餘額通知
- ️ **資源管理**：限制每位使用者最多監控10門課程，並使用執行緒安全機制
-  **容錯處理**：自動重試機制與錯誤恢復功能
- **定期清理監控**：開學後自動刪除監控課程

##  系統架構

### 核心元件

- **CourseQuery 類別**：處理東吳大學系統驗證與課程資料擷取
- **監控引擎**：多執行緒背景監控，每3秒檢查一次課程狀況
- **LINE Bot 整合**：Webhook 處理與推播通知傳送
- **Flask Web 服務**：RESTful API 端點與健康監控儀表板
- **後端框架**：Flask 3.1.1
- **網頁爬蟲**：requests 2.32.4 + BeautifulSoup 4.13.4
- **訊息平台**：LINE Bot SDK 3.17.1
- **並發處理**：Python threading 配合執行緒安全鎖
- **資料解析**：正規表示式 + DOM 解析
- **環境管理**：python-dotenv 1.0.0

## 如何自行使用

### 使用方式選擇

**方法一：本地開發**
- 需要安裝 Python 環境
- 使用 ngrok 建立連接通道
- 適合開發和測試階段

**方法二：雲端部署**
- 無需本地環境，24小時運行
- 使用 Railway 免費部署
- 適合正式運行和長期監控

### 環境需求 (本地開發)

- **Python 3.7+** 並安裝 pip 套件管理器
- **LINE Bot 頻道** (Channel Access Token 與 Channel Secret)
- **東吳大學帳號** (學生認證資料)
- **ngrok** 用於local開發時的HTTPS連接通道

### 安裝指南 (本地開發)

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

服務就可以在 `http://localhost:5000` 上運行

##  ngrok 設定與整合

### 安裝 ngrok

1. **下載 ngrok**
   - 前往 [ngrok.com](https://ngrok.com/) 並建立免費帳號
   - 下載適用於您作業系統的版本

2. **認證設定**
```bash
ngrok authtoken 您的_認證_TOKEN
```

### 連接通道設定

1. **啟動您的 Flask 應用程式**
```bash
python main.py
```

2. **建立 HTTP 連接通道 (開新終端機)**
```bash
ngrok http 5000
```

3. **複製 HTTPS 網址 (Forwarding那行)**
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
   - 設定 **Webhook URL**：`https://abc123.ngrok.io/callback` **(記得要加/callback)**
   - 啟用 **Use webhook**
   - 點擊 **Verify** 測試連線

3. **測試您的機器人**
   - 使用 QR code 加入機器人為好友
   - 發送測試訊息

## 雲端部署方式 

### 雲端部署需求

- **GitHub 帳號** (免費註冊)
- **Railway 帳號** (免費註冊：https://railway.app)
- **LINE Bot 頻道資訊** (同本地開發)
- **東吳大學帳號** (同本地開發)

### Railway 部署步驟

#### 步驟 1: 準備程式碼

1. **建立 GitHub Repository**
   - 前往 https://github.com 並登入
   - 點擊 "New repository"
   - Repository 名稱：`soochow-course-bot`
   - 設為 Public 或 Private
   - 點擊 "Create repository"

2. **上傳程式碼到 GitHub**
   - 下載專案檔案
   - 上傳所有檔案到 GitHub (除了 .env 檔案)

#### 步驟 2: Railway 部署

1. **登入 Railway**
   - 前往 https://railway.app
   - 使用 GitHub 帳號登入

2. **建立新專案**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇你的 Repository
   - 點擊 "Deploy Now"

3. **設定環境變數**
   - 在 Railway Dashboard 點擊你的專案
   - 進入 "Variables" 分頁
   - 新增以下環境變數：
     ```
     LINE_CHANNEL_ACCESS_TOKEN=你的_LINE_Token
     LINE_CHANNEL_SECRET=你的_LINE_Secret
     SOOCHOW_USERNAME=你的東吳學號
     SOOCHOW_PASSWORD=你的東吳密碼
     ```

#### 步驟 3: 設定 LINE Webhook

1. **取得 Railway 網址**
   - 在專案設定中點擊 "Generate Domain"
   - 複製網址 (例如：`https://your-app.up.railway.app`)

2. **更新 LINE Bot 設定**
   - 前往 LINE Developers Console
   - 設定 Webhook URL：`https://your-app.up.railway.app/callback`
   - 啟用 "Use webhook" 並驗證

## 機器人指令與使用方式

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

### 系統參數

```python
MONITOR_INTERVAL = 3              # 監控間隔（秒）
MAX_MONITORING_PER_USER = 10      # 每用戶最大監控課程數
REQUEST_TIMEOUT = 30              # HTTP 請求超時時間
PORT = 5000                       # Flask 伺服器埠號
```

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

## 免責聲明

此機器人僅供**教育和個人使用**。使用者必須遵守東吳大學的服務條款和相關規定。

開發者對任何誤用或違規行為不承擔責任。

---

為東吳大學學生製作(如有問題歡迎私訊問我，我會盡量回答!)