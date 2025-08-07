# 🤖 Soochow University Course Monitoring Bot

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)](https://flask.palletsprojects.com/)
[![LINE Bot SDK](https://img.shields.io/badge/LINE%20Bot%20SDK-3.17.1-00C300.svg)](https://github.com/line/line-bot-sdk-python)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A robust **LINE Bot** application designed for **Soochow University** students to monitor course availability in real-time. The system automatically tracks course enrollment status and sends instant notifications when seats become available.

[繁體中文](README_zh.md) | **English**

## ✨ Key Features

- 🔍 **Real-time Course Queries**: Instant course information retrieval using 4-digit course codes
- 🎯 **Intelligent Auto-Monitoring**: Automatically monitors courses with no available seats
- 📋 **Comprehensive Management**: View, add, and remove courses from monitoring lists
- ⚡ **Instant Push Notifications**: LINE message alerts when seats become available
- 🛡️ **Resource Management**: Rate limiting (10 courses per user) and thread-safe operations
- 🔄 **Fault Tolerance**: Automatic retry mechanisms and error recovery

## 🏗️ System Architecture

### Core Components

- **CourseQuery Class**: Handles Soochow University system authentication and course data retrieval
- **Monitoring Engine**: Multi-threaded background monitoring with 5-second intervals
- **LINE Bot Integration**: Webhook handling and push notification delivery
- **Flask Web Service**: RESTful API endpoints and health monitoring dashboard

### Technical Stack

- **Backend Framework**: Flask 3.1.1
- **Web Scraping**: requests 2.32.4 + BeautifulSoup 4.13.4
- **Messaging Platform**: LINE Bot SDK 3.17.1
- **Concurrent Processing**: Python threading with thread-safe locks
- **Data Parsing**: Regular expressions + DOM parsing
- **Environment Management**: python-dotenv 1.0.0

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** with pip package manager
- **LINE Bot Channel** (Channel Access Token & Channel Secret)
- **Soochow University Account** (Student credentials)
- **ngrok** for local development tunneling

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

4. **Environment Configuration**

Create a `.env` file in the project root:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret
SOOCHOW_USERNAME=your_soochow_username
SOOCHOW_PASSWORD=your_soochow_password
```

5. **Start the Application**
```bash
python main.py
```

The service will be available at `http://localhost:5000`

## 🌐 ngrok Setup & Integration

### Install ngrok

1. **Download ngrok**
   - Visit [ngrok.com](https://ngrok.com/) and create a free account
   - Download the appropriate version for your OS

2. **Authentication**
```bash
ngrok authtoken YOUR_AUTH_TOKEN
```

### Tunnel Configuration

1. **Start Your Flask App**
```bash
python main.py
```

2. **Create HTTP Tunnel (New Terminal)**
```bash
ngrok http 5000
```

3. **Copy the HTTPS URL**
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

### LINE Bot Webhook Setup

1. **Navigate to LINE Developers Console**
   - Go to [developers.line.biz](https://developers.line.biz/)
   - Select your channel

2. **Update Webhook URL**
   - Navigate to **Messaging API** tab
   - Set **Webhook URL**: `https://abc123.ngrok.io/callback`
   - Enable **Use webhook**
   - Click **Verify** to test connection

3. **Test Your Bot**
   - Add your bot as a friend using QR code
   - Send a test message

### Production Deployment

For production environments, consider:
- **Paid ngrok Plan** ($8/month) for stable URLs
- **Cloud Hosting**: Railway, Render, or DigitalOcean
- **Domain & SSL**: Custom domain with HTTPS certificate

## 📱 Bot Commands & Usage

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `[4-digit code]` | Query course and auto-monitor if no seats | `7002` |
| `清單` or `list` | View current monitoring list | `清單` |
| `取消 [course_id]` | Cancel monitoring for specific course | `取消 7002` |
| `取消 全部` | Cancel all monitoring | `取消 全部` |
| `幫助` or `help` | Show usage instructions | `幫助` |

### Workflow

1. **Course Query**: Send 4-digit course code to bot
2. **Auto-Monitoring**: System automatically monitors courses with no available seats
3. **Instant Notification**: Receive LINE notification when seats become available
4. **Auto-Cleanup**: Monitoring automatically stops after successful notification

### Response Examples

**Available Seats:**
```
課程名稱：資料結構
選課編號：7002
科目代碼：CSIE2001
學分數：3
修課人數：45/60
剩餘名額：15 人
(目前有15個名額，請盡快去加選!)
```

**No Seats (Auto-Monitoring Activated):**
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

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | ✅ |
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | ✅ |
| `SOOCHOW_USERNAME` | Soochow University Student ID | ✅ |
| `SOOCHOW_PASSWORD` | Soochow University Password | ✅ |

### System Parameters

```python
MONITOR_INTERVAL = 5              # Monitoring interval (seconds)
MAX_MONITORING_PER_USER = 10      # Maximum courses per user
REQUEST_TIMEOUT = 30              # HTTP request timeout
PORT = 5000                       # Flask server port
```

## 📊 Monitoring Mechanism

### Algorithm

1. **Query Cycle**: Check course status every 5 seconds
2. **Availability Detection**: Compare current enrollment vs. capacity
3. **Notification Trigger**: Send LINE push message when seats available
4. **Auto-Termination**: Remove course from monitoring after notification

### Data Structure

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

### Thread Safety

- **Monitoring Lock**: `threading.Lock()` for concurrent access protection
- **Daemon Threads**: Background monitoring threads automatically terminate with main process
- **Resource Cleanup**: Automatic thread termination when monitoring is cancelled

## 🚀 Deployment Options

### Local Development
```bash
python main.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t soochow-course-bot .
docker run -p 5000:5000 --env-file .env soochow-course-bot
```

### Cloud Platforms

**Railway.app**
1. Connect GitHub repository
2. Add environment variables
3. Deploy automatically

**Render.com**
1. Create new web service
2. Connect repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`

## 🔍 Troubleshooting

### Common Issues

**Login Failures**
- Verify Soochow University credentials
- Check if the university system is accessible
- Ensure VPN connection if accessing remotely

**LINE Bot Unresponsive**
- Validate Channel Access Token and Secret
- Verify webhook URL configuration
- Check ngrok tunnel status
- Review Flask application logs

**Course Query Errors**
- Confirm 4-digit course code format
- Verify course exists in current semester
- Check if course registration is open

**Monitoring Not Working**
- Ensure credit card is linked to LINE Developers account
- Check Push Message API quotas
- Verify thread execution in logs

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
- Monitoring state changes
- Error messages and stack traces

## 🧪 Testing

### Unit Testing
```bash
# Install testing dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/
```

### Manual Testing
1. **Health Check**: Visit `http://localhost:5000`
2. **Course Query**: Send course code to LINE bot
3. **Monitoring**: Verify background thread execution
4. **Notifications**: Test push message delivery

## 📈 Performance & Scalability

### Monitoring Capacity
- **Per User**: Maximum 10 concurrent course monitors
- **System**: Theoretical limit depends on server resources
- **Threads**: One monitoring thread per course per user

### Optimization Techniques
- **Session Reuse**: Persistent HTTP sessions for authentication
- **Thread Pools**: Consider implementing thread pools for high user volumes
- **Database Integration**: Store monitoring data in persistent storage for scalability
- **Caching**: Implement course data caching to reduce server load

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup
```bash
git clone https://github.com/yourusername/soochow-course-bot.git
cd soochow-course-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Contribution Process
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to functions and classes
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This bot is intended for **educational and personal use only**. Users must comply with Soochow University's terms of service and regulations. The developers assume no responsibility for any misuse or violations.

**Important Notes:**
- Respect the university's course registration system
- Do not overload servers with excessive requests
- Use responsibly during peak registration periods
- Ensure compliance with academic integrity policies

## 📞 Support & Feedback

- **Issues**: [GitHub Issues](https://github.com/yourusername/soochow-course-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/soochow-course-bot/discussions)
- **Email**: your.email@example.com

## 🙏 Acknowledgments

- **Soochow University** for providing the course system
- **LINE Corporation** for the messaging platform
- **Contributors** who helped improve this project
- **Open Source Community** for the amazing libraries

---

Made with ❤️ for Soochow University students