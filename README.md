# 🤖 東吳課程餘額監控機器人

一個基於 LINE Bot 的東吳大學課程餘額即時監控系統，當額滿課程出現名額時會立即推送通知。

## ✨ 功能特色

### 🔍 **課程查詢**
- 即時查詢課程餘額狀態
- 支援體育課程和通識課程
- 顯示詳細課程資訊（人數、名額、開課班級等）

### 📋 **智能監控**
- 額滿課程自動加入監控清單
- 背景持續監控，有名額立即通知
- 支援同時監控多門課程

### 🔔 **即時通知**
- LINE 推播通知，不錯過任何機會
- 詳細課程資訊，包含選課編號和科目代碼
- 通知後自動移除監控，避免重複提醒

### 🛡️ **系統保護**
- 速率限制防止濫用
- 用戶監控數量上限
- 自動重連和錯誤恢復
- 完整日誌記錄

## 🚀 快速開始

### 前置需求

- Python 3.7+
- LINE Bot 開發者帳號
- 東吳大學校務系統帳號

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd soochow-course-monitor
```

2. **建立虛擬環境**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
```

4. **設定環境變數**
```bash
# 複製環境變數模板
cp .env.txt .env

# 編輯 .env 檔案，填入您的設定
nano .env
```

5. **啟動機器人**
```bash
python main.py
```

## ⚙️ 環境變數設定

在 `.env` 檔案中設定以下變數：

### 必要設定
```bash
# LINE Bot API
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_CHANNEL_SECRET=your_channel_secret

# 東吳校務系統
SOOCHOW_USERNAME=your_student_id
SOOCHOW_PASSWORD=your_password
```

### 選用設定
```bash
# 監控設定
MONITOR_INTERVAL=5                    # 監控間隔（秒）
MAX_RETRY_ATTEMPTS=3                  # 重試次數
REQUEST_TIMEOUT=30                    # 請求逾時（秒）

# 伺服器設定
PORT=5000                            # Web 伺服器埠號
HOST=0.0.0.0                        # 綁定地址

# 資料庫設定
DATABASE_NAME=course_monitor.db       # 資料庫檔名

# 日誌設定
LOG_LEVEL=INFO                       # 日誌等級
LOG_FILE=course_monitor.log          # 日誌檔案

# 系統限制
MAX_MONITORING_PER_USER=10           # 單用戶監控上限
RATE_LIMIT_PER_MINUTE=20             # 速率限制
DEBUG_MODE=false                     # 除錯模式
```

## 📱 LINE Bot 設定

### 1. 建立 LINE Bot
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立新的 Provider 和 Channel
3. 取得 `Channel Access Token` 和 `Channel Secret`

### 2. 設定 Webhook
1. 在 LINE Developers Console 中設定 Webhook URL：
   ```
   https://your-domain.com/callback
   ```
2. 啟用 Webhook
3. 關閉自動回覆訊息

### 3. 取得 Bot 資訊
- 掃描 QR Code 或搜尋 Bot ID 加入好友

## 🎯 使用方法

### 基本指令

| 指令格式 | 功能說明 | 範例 |
|---------|---------|------|
| `[類別] [課程代碼]` | 查詢課程餘額 | `體育 7002` |
| `清單` | 查看監控清單 | `清單` |
| `取消 [課程代碼]` | 取消監控特定課程 | `取消 7002` |
| `取消 全部` | 取消所有監控 | `取消 全部` |
| `測試` | 檢查系統狀態 | `測試` |

### 支援課程類別

- **體育** - 體育課程
- **通識** - 通識教育課程

### 使用流程

1. **查詢課程**：輸入 `體育 7002`
   - 有名額：顯示詳細資訊
   - 額滿：自動加入監控

2. **監控通知**：課程有名額時自動推送

3. **管理監控**：使用 `清單` 查看，`取消` 移除

## 🏗️ 系統架構

### 核心模組

```
main.py
├── CourseMonitor          # 核心監控邏輯
├── DatabaseManager        # 資料庫管理
├── InputValidator         # 輸入驗證
├── RateLimiter           # 速率限制
└── Flask App             # Web 介面
```

### 資料庫設計

#### monitoring 表
```sql
CREATE TABLE monitoring (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    category TEXT NOT NULL,
    course_name TEXT,
    status TEXT DEFAULT 'full',
    created_at TIMESTAMP,
    last_check TIMESTAMP
);
```

#### query_history 表
```sql
CREATE TABLE query_history (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    category TEXT NOT NULL,
    course_name TEXT,
    current_count INTEGER,
    max_count INTEGER,
    available INTEGER,
    query_time TIMESTAMP
);
```

## 🔧 API 端點

### Web 介面
- `GET /` - 系統狀態頁面
- `POST /callback` - LINE Bot Webhook
- `GET /health` - 健康檢查

### 健康檢查回應範例
```json
{
    "status": "healthy",
    "login_status": true,
    "monitoring_count": 15,
    "last_login_time": "2024-01-15T10:30:00",
    "timestamp": "2024-01-15T14:25:30"
}
```

## 📊 系統限制

| 項目 | 限制 | 說明 |
|------|------|------|
| 監控上限 | 10 門課程/用戶 | 防止系統過載 |
| 請求頻率 | 20 次/分鐘 | 防止濫用 |
| 監控頻率 | 每 5 秒 | 平衡即時性與系統負載 |
| 資料保留 | 30 天 | 自動清理舊查詢記錄 |
| 請求逾時 | 30 秒 | 防止長時間等待 |

## 🛠️ 進階配置

### Docker 部署

1. **建立 Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "main.py"]
```

2. **建置映像**
```bash
docker build -t soochow-course-monitor .
```

3. **執行容器**
```bash
docker run -d \
  --name course-monitor \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  soochow-course-monitor
```

### 使用 Systemd 服務

1. **建立服務檔案** `/etc/systemd/system/course-monitor.service`
```ini
[Unit]
Description=Soochow Course Monitor Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/soochow-course-monitor
Environment=PATH=/path/to/soochow-course-monitor/venv/bin
ExecStart=/path/to/soochow-course-monitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. **啟動服務**
```bash
sudo systemctl daemon-reload
sudo systemctl enable course-monitor
sudo systemctl start course-monitor
```

### 反向代理設定（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📝 開發指南

### 專案結構
```
soochow-course-monitor/
├── main.py                 # 主程式
├── requirements.txt        # 依賴清單
├── .env.txt               # 環境變數模板
├── .gitignore             # Git 忽略檔案
├── README.md              # 說明文件
├── course_monitor.db      # SQLite 資料庫
├── course_monitor.log     # 日誌檔案
└── venv/                  # 虛擬環境
```

### 新增課程類別

1. **修改課程類別字典**
```python
COURSE_CATEGORIES = {
    '通識': '07:通識',
    '體育': '05:體育',
    '新類別': 'XX:新類別參數'  # 新增這行
}
```

2. **更新驗證器**
```python
@staticmethod
def validate_category(category):
    valid_categories = ['通識', '體育', '新類別']  # 加入新類別
    if category not in valid_categories:
        raise ValidationError(f"不支援的課程類別：{category}")
    return category
```

### 自定義通知格式

修改 `send_notification` 方法：
```python
def send_notification(self, user_id, course_info):
    message = f"""🎉 【{course_info['category']}課程】有名額了！
    
📚 {course_info['course_name']}
🔢 選課編號：{course_info['course_number']}
👥 名額：{course_info['available']} 人

⚡ 立即前往選課！"""
    
    # 發送邏輯...
```

## 🐛 故障排除

### 常見問題

#### 1. 登入失敗
**症狀**：顯示 "東吳系統登入失敗"
**解決方法**：
- 檢查 `SOOCHOW_USERNAME` 和 `SOOCHOW_PASSWORD` 是否正確
- 確認東吳校務系統是否正常運作
- 檢查網路連線

#### 2. LINE Bot 無回應
**症狀**：LINE Bot 不回覆訊息
**解決方法**：
- 檢查 Webhook URL 是否正確設定
- 確認 `LINE_CHANNEL_ACCESS_TOKEN` 和 `LINE_CHANNEL_SECRET` 正確
- 查看日誌檔案 `course_monitor.log`

#### 3. 資料庫錯誤
**症狀**：出現 SQLite 相關錯誤
**解決方法**：
- 檢查檔案權限
- 刪除 `course_monitor.db` 讓系統重新建立
- 確認磁碟空間充足

#### 4. 記憶體使用過高
**症狀**：系統記憶體使用量持續增長
**解決方法**：
- 檢查監控課程數量
- 調整 `MONITOR_INTERVAL` 增加間隔時間
- 重新啟動服務

### 除錯模式

啟用除錯模式：
```bash
# 在 .env 檔案中設定
DEBUG_MODE=true
```

或臨時啟用：
```bash
DEBUG_MODE=true python main.py
```

### 日誌分析

日誌等級說明：
- `INFO`：一般資訊
- `WARNING`：警告訊息
- `ERROR`：錯誤訊息
- `CRITICAL`：嚴重錯誤

查看即時日誌：
```bash
tail -f course_monitor.log
```

## 📈 監控和維護

### 系統監控

1. **健康檢查**
```bash
curl http://localhost:5000/health
```

2. **監控指標**
- 登入狀態
- 監控課程數量
- 上次登入時間
- 系統運行時間

### 定期維護

1. **日誌輪轉**
```bash
# 建立 logrotate 設定 /etc/logrotate.d/course-monitor
/path/to/course_monitor.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    postrotate
        systemctl reload course-monitor
    endscript
}
```

2. **資料庫備份**
```bash
# 每日備份腳本
#!/bin/bash
cp course_monitor.db "backup/course_monitor_$(date +%Y%m%d).db"
find backup/ -name "*.db" -mtime +7 -delete
```

3. **效能監控**
```bash
# 監控腳本
#!/bin/bash
ps aux | grep "python main.py"
du -h course_monitor.db
tail -n 100 course_monitor.log | grep ERROR
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 開發環境設定

1. Fork 專案
2. 建立功能分支：`git checkout -b feature/new-feature`
3. 安裝開發依賴：`pip install -r requirements-dev.txt`
4. 進行修改並測試
5. 提交變更：`git commit -m "Add new feature"`
6. 推送到分支：`git push origin feature/new-feature`
7. 建立 Pull Request

### 程式碼規範

- 使用 Black 格式化：`black main.py`
- 通過 Flake8 檢查：`flake8 main.py`
- 添加適當的註解和文檔

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## ⚠️ 免責聲明

- 本機器人僅供學術研究和個人使用
- 請遵守東吳大學相關規定和使用條款
- 作者不對因使用本機器人造成的任何後果負責
- 請合理使用，避免對學校系統造成負擔

## 📞 支援與聯絡

- 問題回報：[GitHub Issues](https://github.com/your-repo/issues)
- 功能建議：[GitHub Discussions](https://github.com/your-repo/discussions)
- 電子郵件：your-email@example.com

## 🎯 未來計劃

- [ ] 支援更多課程類別
- [ ] 新增課程評價查詢
- [ ] 實作課表衝突檢查
- [ ] 支援多校系統
- [ ] 新增 Web 管理介面
- [ ] 實作推播通知設定
- [ ] 支援課程收藏功能

---

<div align="center">

**⭐ 如果這個專案對您有幫助，請給我們一個 Star！**

Made with ❤️ for SCU students

</div>