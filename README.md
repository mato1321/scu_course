# Course Warrior🦸 (Soochow University Course Availability Bot)

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.17.1-00C300.svg)](https://github.com/line/line-bot-sdk-python)

This is a LINE bot application exclusively for Soochow University students that can monitor course availability in real-time. The system automatically tracks course enrollment status and sends immediate notifications when spots become available.

**English** | [繁體中文](README_zh.md)

## Core Features

- **Real-time Course Query**: Quickly query detailed course information using 4-digit course codes
- **Smart Auto-monitoring**: Automatically monitors full courses and notifies immediately when spots open up
- **Complete Management Interface**: View, add, and remove courses from your monitoring list
- **Instant Push Notifications**: Receive availability notifications through LINE messages in real-time
- **Resource Management**: Limits each user to monitoring a maximum of 10 courses with thread-safe mechanisms
- **Fault Tolerance**: Automatic retry mechanisms and error recovery features
- **Scheduled Monitor Cleanup**: Automatically deletes monitored courses after semester begins

## System Architecture

### Core Components

- **CourseQuery Class**: Handles Soochow University system authentication and course data extraction
- **Monitoring Engine**: Multi-threaded background monitoring, checking course status every 3 seconds
- **LINE Bot Integration**: Webhook handling and push notification delivery
- **Flask Web Service**: RESTful API endpoints and health monitoring dashboard
- **Backend Framework**: Flask 3.1.1
- **Web Scraping**: requests 2.32.4 + BeautifulSoup 4.13.4
- **Messaging Platform**: LINE Bot SDK 3.17.1
- **Concurrency Handling**: Python threading with thread-safe locks
- **Data Parsing**: Regular expressions + DOM parsing
- **Environment Management**: python-dotenv 1.0.0

## How to Use

### Usage Options

**Method 1: Local Development**
- Requires Python environment installation
- Uses ngrok to establish connection tunnel
- Suitable for development and testing phases

**Method 2: Cloud Deployment**
- No local environment needed, runs 24/7
- Uses Railway for free deployment
- Suitable for production and long-term monitoring

### Environment Requirements (Local Development)

- **Python 3.7+** with pip package manager installed
- **LINE Bot Channel** (Channel Access Token and Channel Secret)
- **Soochow University Account** (student authentication credentials)
- **ngrok** for HTTPS tunnel during local development

### Installation Guide (Local Development)

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/soochow-course-bot.git
cd soochow-course-bot
```

2. **Create Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Variables Setup**

Create a `.env` file in the project root directory:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
SOOCHOW_USERNAME=your_soochow_university_student_id
SOOCHOW_PASSWORD=your_soochow_university_password
```

5. **Start Application**
```bash
python main.py
```

The service will run on `http://localhost:5000`

## ngrok Setup and Integration

### Install ngrok

1. **Download ngrok**
   - Go to [ngrok.com](https://ngrok.com/) and create a free account
   - Download the version for your operating system

2. **Authentication Setup**
```bash
ngrok authtoken your_auth_token
```

### Tunnel Setup

1. **Start Your Flask Application**
```bash
python main.py
```

2. **Create HTTP Tunnel (Open new terminal)**
```bash
ngrok http 5000
```

3. **Copy HTTPS URL (from Forwarding line)**
```
ngrok by @inconshreveable

Session Status    online
Account           your_account (Plan: Free)
Version           2.3.40
Region            United States (us)
Web Interface     http://127.0.0.1:4040
Forwarding        http://abc123.ngrok.io -> http://localhost:5000
Forwarding        https://abc123.ngrok.io -> http://localhost:5000  <-- Use this URL
```

### LINE Bot Webhook Configuration

1. **Go to LINE Developers Console**
   - Visit [developers.line.biz](https://developers.line.biz/)
   - Select your channel

2. **Update Webhook URL**
   - Navigate to **Messaging API** tab
   - Set **Webhook URL**: `https://abc123.ngrok.io/callback` **(remember to add /callback)**
   - Enable **Use webhook**
   - Click **Verify** to test connection

3. **Test Your Bot**
   - Add the bot as a friend using QR code
   - Send test messages

## Cloud Deployment Method

### Cloud Deployment Requirements

- **GitHub Account** (free registration)
- **Railway Account** (free registration: https://railway.app)
- **LINE Bot Channel Information** (same as local development)
- **Soochow University Account** (same as local development)

### Railway Deployment Steps

#### Step 1: Prepare Code

1. **Create GitHub Repository**
   - Go to https://github.com and log in
   - Click "New repository"
   - Repository name: `soochow-course-bot`
   - Set as Public or Private
   - Click "Create repository"

2. **Upload Code to GitHub**
   - Download project files
   - Upload all files to GitHub (except .env file)

#### Step 2: Railway Deployment

1. **Login to Railway**
   - Go to https://railway.app
   - Use GitHub account to log in

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Repository
   - Click "Deploy Now"

3. **Configure Environment Variables**
   - In Railway Dashboard, click your project
   - Go to "Variables" tab
   - Add the following environment variables:
     ```
     LINE_CHANNEL_ACCESS_TOKEN=your_LINE_Token
     LINE_CHANNEL_SECRET=your_LINE_Secret
     SOOCHOW_USERNAME=your_soochow_student_id
     SOOCHOW_PASSWORD=your_soochow_password
     ```

#### Step 3: Configure LINE Webhook

1. **Get Railway URL**
   - In project settings, click "Generate Domain"
   - Copy the URL (e.g., `https://your-app.up.railway.app`)

2. **Update LINE Bot Settings**
   - Go to LINE Developers Console
   - Set Webhook URL: `https://your-app.up.railway.app/callback`
   - Enable "Use webhook" and verify

## Bot Commands and Usage

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `[4-digit code]` | Query course and auto-monitor if no spots available | `7002` |
| `清單` | View current monitoring list | `清單` |
| `取消 [course code]` | Cancel monitoring for specific course | `取消 7002` |
| `取消 全部` | Cancel all monitoring | `取消 全部` |
| `幫助` | Display help instructions | `幫助` |

### Workflow

1. **Course Query**: Send a 4-digit course code to the bot
2. **Auto-monitoring**: System automatically monitors courses with no available spots
3. **Instant Notification**: Receive LINE notifications when spots become available
4. **Auto Cleanup**: Automatically stops monitoring after successful notification

### Response Examples

**Spots Available:**
```
課程名稱：資料結構
選課編號：7002
科目代碼：CSIE2001
學分數：3
修課人數：45/60
剩餘名額：15 人
(目前有15個名額，請盡快去加選!)
```

**No Spots (Auto-monitoring Activated):**
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

### System Parameters

```python
MONITOR_INTERVAL = 3              # Monitoring interval (seconds)
MAX_MONITORING_PER_USER = 10      # Maximum monitored courses per user
REQUEST_TIMEOUT = 30              # HTTP request timeout
PORT = 5000                       # Flask server port
```

### Debugging

**Enable Debug Mode**
```python
DEBUG_MODE = True
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Log Analysis**
The system outputs detailed execution logs:
- Authentication status
- Course query results
- Monitoring status changes
- Error messages and stack traces

## Disclaimer

This bot is for **educational and personal use only**. Users must comply with Soochow University's terms of service and related regulations.

The developer assumes no responsibility for any misuse or violations.

---

Made for Soochow University students (If you have any questions, feel free to message me privately and I'll try my best to answer!)