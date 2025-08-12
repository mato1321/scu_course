# Course Warrior🦸<br>(Soochow University Course Availability Bot)

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.17.1-00C300.svg)](https://github.com/line/line-bot-sdk-python)

This is a LINE bot application exclusively for Soochow University students that can monitor course availability in real-time. The system automatically tracks course enrollment status and sends immediate notifications when spots become available.

**English** | [繁體中文](README_zh.md)

## Core Features

- **Real-time Course Query**: Quickly query detailed course information using 4-digit course codes
-  **Smart Auto-monitoring**: Automatically monitors full courses and notifies immediately when spots open up
-  **Complete Management Interface**: View, add, and remove courses from your monitoring list
-  **Instant Push Notifications**: Receive availability notifications through LINE messages in real-time
-  **Resource Management**: Limits each user to monitoring a maximum of 10 courses with thread-safe mechanisms
-  **Fault Tolerance**: Automatic retry mechanisms and error recovery features
-  **Scheduled Monitor Cleanup**: Automatically deletes monitored courses after semester begins

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

##  How to Use

### Environment Requirements (for local development)

- **Python 3.7+** with pip package manager installed
- **LINE Bot Channel** (Channel Access Token and Channel Secret)
- **Soochow University Account** (student authentication credentials)
- **ngrok** for HTTPS tunnel during local development

### Installation Guide

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

##  ngrok Setup and Integration

### Install ngrok

1. **Download ngrok**
   - Go to [ngrok.com](https://ngrok.com/) and create a free account
   - Download the version for your operating system

2. **Authentication Setup**
```bash
ngrok authtoken YOUR_AUTH_TOKEN
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

##  Bot Commands and Usage

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
Course Name: Data Structures
Course Code: 7002
Subject Code: CSIE2001
Credits: 3
Enrollment: 45/60
Available Spots: 15 people
(Currently 15 spots available, please add the course quickly!)
```

**No Spots (Auto-monitoring Activated):**
```
Successfully added to monitoring list!
Course Name: Data Structures
Course Code: 7002
Subject Code: CSIE2001
Credits: 3
Enrollment: 60/60
Available Spots: 0 people
(Currently no spots available, you will be notified via LINE when spots open up)
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

##  Disclaimer

This bot is for **educational and personal use only**. Users must comply with Soochow University's terms of service and related regulations.

The developer assumes no responsibility for any misuse or violations.

---

Made for Soochow University students <br>(If you have any questions, feel free to message me privately and I'll try my best to answer!)