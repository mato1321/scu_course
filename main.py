import os
import requests
from bs4 import BeautifulSoup
import re
import threading
import time
import json
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setting
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
SOOCHOW_USERNAME = os.getenv('SOOCHOW_USERNAME')
SOOCHOW_PASSWORD = os.getenv('SOOCHOW_PASSWORD')
MONITOR_INTERVAL = 3
MAX_RETRY_ATTEMPTS = 3
REQUEST_TIMEOUT = 30
PORT = 5000
HOST = '0.0.0.0'
MAX_MONITORING_PER_USER = 10
RATE_LIMIT_PER_MINUTE = 20
DEBUG_MODE = False
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
monitoring_data = {}  # {user_id: {course_id: {'course_name': str, 'thread': Thread}}}
monitoring_lock = threading.Lock()


class CourseQuery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logged_in = False

    def login(self):
        """Login to Soochow University system"""
        try:
            # get login page
            login_url = "https://web.sys.scu.edu.tw/logins.asp"
            self.session.get(login_url)

            # Submit login form
            login_data = {
                'id': SOOCHOW_USERNAME,
                'passwd': SOOCHOW_PASSWORD
            }

            submit_url = "https://web.sys.scu.edu.tw/login0.asp"
            response = self.session.post(submit_url, data=login_data)
            content = response.content.decode('big5', errors='ignore')
            if "登入成功" in content:
                self.logged_in = True
                print("Login successful")
                return True
            else:
                print("Login failed")
                return False

        except Exception as e:
            print(f"Error: {e}")
            return False

    def query_course(self, course_id):
        """Check course availability"""
        if not self.logged_in:
            if not self.login():
                return {"error": "Please check your SOOCHOW_USERNAME and SOOCHOW_PASSWORD environment variables."}

        try:
            print(f"Querying course {course_id}")

            # Visit the query page first
            query_page_url = "https://web.sys.scu.edu.tw/course201.asp"
            self.session.get(query_page_url)

            # Submit to course202.asp
            submit_url = "https://web.sys.scu.edu.tw/course202.asp"
            query_data = {
                'syear': '114',
                'smester': '1',
                'classid': course_id
            }

            print(f"Submitting query data: {query_data}")
            response = self.session.post(submit_url, data=query_data)
            content = response.content.decode('big5', errors='ignore')

            print(f"Received response, length: {len(content)} characters")

            # Parse results
            return self.parse_result(content, course_id)

        except Exception as e:
            print(f"Query error: {e}")
            return {"error": f"Query error: {e}"}

    def parse_result(self, content, course_id):
        """Parse query results"""
        try:
            print(f"Starting to parse course {course_id}")

            # Check for error messages
            if "查無此課程" in content or "課程不存在" in content:
                return {"error": f"Course not found: {course_id}"}

            # Check if course ID is found
            if course_id not in content:
                print(f"Course ID {course_id} not found in response")
                return {"error": f"Course {course_id} not found in query results"}

            soup = BeautifulSoup(content, 'html.parser')

            # Find tables containing course data
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    # Check each cell for course ID
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if course_id in cell_text:
                            print(f"Found cell containing course ID: {cell_text}")

                            # Try to parse course information
                            result = self.extract_course_info(cell_text, course_id)
                            if result:
                                return result

            return {"error": f"Found course ID {course_id} but unable to parse detailed information"}

        except Exception as e:
            print(f"Parse error: {e}")
            return {"error": f"Error occurred while parsing results: {e}"}

    def extract_course_info(self, text, course_id):
        """Extract course information"""
        try:
            print(f"Parsing text: {text}")

            # Create regex pattern
            pattern = course_id + r'([A-Z0-9]+)([^0-9]+)(\d+)'
            match = re.search(pattern, text)

            if match:
                course_code = match.group(1)
                course_name = match.group(2).strip()
                numbers = match.group(3)

                print(f"Course code: {course_code}")
                print(f"Course name: {course_name}")
                print(f"Numbers part: {numbers}")

                # Parse numbers part
                credits, max_students, current_students = self.parse_numbers(numbers)
                available = max_students - current_students

                print(f"Credits: {credits}, Max: {max_students}, Current: {current_students}, Available: {available}")

                # Return structured data
                return {
                    "course_name": course_name,
                    "course_id": course_id,
                    "course_code": course_code,
                    "credits": credits,
                    "current_students": current_students,
                    "max_students": max_students,
                    "available": available
                }

            # If first regex fails, try other methods
            remaining_text = text[len(course_id):]

            # Find course code
            code_match = re.search(r'^([A-Z0-9]{6,10})', remaining_text)
            if code_match:
                course_code = code_match.group(1)
                rest_text = remaining_text[len(course_code):]

                # Find trailing numbers
                numbers_pattern = r'(\d+)$'
                numbers_match = re.search(numbers_pattern, rest_text)
                if numbers_match:
                    numbers = numbers_match.group(1)
                    course_name = rest_text[:rest_text.rfind(numbers)].strip()

                    credits, max_students, current_students = self.parse_numbers(numbers)
                    available = max_students - current_students

                    return {
                        "course_name": course_name,
                        "course_id": course_id,
                        "course_code": course_code,
                        "credits": credits,
                        "current_students": current_students,
                        "max_students": max_students,
                        "available": available
                    }

            return None

        except Exception as e:
            print(f"Course info extraction error: {e}")
            return None

    def format_result(self, course_data):
        """Format results"""
        if course_data.get("error"):
            return course_data["error"]

        available = course_data["available"]
        course_name = course_data["course_name"]
        course_id = course_data["course_id"]
        course_code = course_data["course_code"]
        credits = course_data["credits"]
        current_students = course_data["current_students"]
        max_students = course_data["max_students"]

        if available <= 0:
            # Format for no available slots
            result = f"""課程名稱：{course_name}
選課編號：{course_id}
科目代碼：{course_code}
學分數：{credits}
修課人數：{current_students}/{max_students}
剩餘名額：{available} 人
(目前沒有名額，當有名額時會由line主動通知)
(可透過"清單"查詢目前的所有監控項目)"""
        else:
            # Format for available slots
            result = f"""課程名稱：{course_name}
選課編號：{course_id}
科目代碼：{course_code}
學分數：{credits}
修課人數：{current_students}/{max_students}
剩餘名額：{available} 人
(目前有{available}個名額，請盡快去加選!)"""

        return result

    def parse_numbers(self, numbers_str):
        """Parse number string to extract credits, max students, current students"""
        try:
            if len(numbers_str) == 5:  # Example: 36060
                credits = int(numbers_str[0])
                max_students = int(numbers_str[1:3])
                current_students = int(numbers_str[3:5])
            elif len(numbers_str) == 4:  # Example: 3660
                credits = int(numbers_str[0])
                max_students = int(numbers_str[1:3])
                current_students = int(numbers_str[2:4])
            elif len(numbers_str) >= 3:
                credits = int(numbers_str[0])
                remaining = numbers_str[1:]
                half = len(remaining) // 2
                max_students = int(remaining[:half]) if half > 0 else 0
                current_students = int(remaining[half:]) if half > 0 else 0
            else:
                credits = int(numbers_str) if numbers_str.isdigit() else 0
                max_students = 0
                current_students = 0

            return credits, max_students, current_students

        except:
            return 0, 0, 0


# Create query object
query = CourseQuery()


def monitor_course(user_id, course_id, course_name):
    """Background thread to monitor course availability"""
    print(f"Starting to monitor course {course_id} ({course_name}) for user {user_id}")

    while True:
        try:
            # Check if still in monitoring list
            with monitoring_lock:
                if (user_id not in monitoring_data or
                        course_id not in monitoring_data[user_id]):
                    print(f"Course {course_id} removed from monitoring, stopping thread")
                    break

            # Query course status
            result = query.query_course(course_id)

            if result and not result.get("error"):
                available = result.get("available", 0)

                if available > 0:
                    # Slots available! Send notification
                    notification = f"""好消息！課程有名額了！

課程名稱：{course_name}
選課編號：{course_id}
剩餘名額：{available} 人

請盡快前往選課系統加選！
系統將自動停止監控此課程。"""

                    try:
                        line_bot_api.push_message(user_id, TextSendMessage(text=notification))
                        print(f"Notification sent to user {user_id}, course {course_id} has {available} slots available")
                    except Exception as e:
                        print(f"Failed to send notification: {e}")

                    # Remove monitoring
                    with monitoring_lock:
                        if user_id in monitoring_data and course_id in monitoring_data[user_id]:
                            del monitoring_data[user_id][course_id]
                            if not monitoring_data[user_id]:  # If user has no other monitored courses
                                del monitoring_data[user_id]

                    break
                else:
                    print(f"Course {course_id} still has no slots available (remaining: {available})")
            else:
                print(f"Failed to query course {course_id}: {result.get('error', 'Unknown error')}")

            # Wait 5 seconds before checking again
            time.sleep(5)

        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            time.sleep(5)

    print(f"Stopped monitoring course {course_id}")


def start_monitoring(user_id, course_id, course_name):
    """Start monitoring a course"""
    with monitoring_lock:
        if user_id not in monitoring_data:
            monitoring_data[user_id] = {}

        # If already monitoring, don't start new thread
        if course_id in monitoring_data[user_id]:
            return False  # Already monitoring

        # Create and start monitoring thread
        monitor_thread = threading.Thread(
            target=monitor_course,
            args=(user_id, course_id, course_name),
            daemon=True
        )

        monitoring_data[user_id][course_id] = {
            'course_name': course_name,
            'thread': monitor_thread
        }

        monitor_thread.start()
        return True


def stop_monitoring(user_id, course_id=None):
    """Stop monitoring course - supports canceling single course or all courses"""
    with monitoring_lock:
        if user_id not in monitoring_data:
            return None, 0

        if course_id is None:  # Cancel all
            courses = monitoring_data[user_id].copy()
            del monitoring_data[user_id]
            return list(courses.values()), len(courses)
        else:  # Cancel single course
            if course_id in monitoring_data[user_id]:
                course_name = monitoring_data[user_id][course_id]['course_name']
                del monitoring_data[user_id][course_id]

                if not monitoring_data[user_id]:  # If user has no other monitored courses
                    del monitoring_data[user_id]

                return course_name, 1

        return None, 0


def get_user_monitoring_list(user_id):
    """Get user's monitoring list"""
    with monitoring_lock:
        if user_id in monitoring_data:
            return monitoring_data[user_id].copy()
        return {}


@app.route("/")
def home():
    return """
    <h1>東吳課程餘額查詢機器人 (增強版)</h1>
    <p>服務運行中</p>
    <p>LINE訊息格式：</p>
    <ul>
        <li><strong>直接輸入4位數課程編號</strong> - 查詢並自動監控</li>
        <li><strong>清單</strong> - 查看監控清單</li>
        <li><strong>取消 課程編號</strong> - 取消單一監控</li>
        <li><strong>取消 全部</strong> - 取消所有監控</li>
        <li><strong>幫助</strong> - 顯示使用說明</li>
    </ul>
    <p>功能：直接查詢課程，無名額時自動監控並通知</p>
    """


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return 'Invalid signature', 400

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message = event.message.text.strip()

    # Help command
    if message in ['幫助', 'help', '說明']:
        help_text = """選修戰士使用說明
此機器人無名額課程自動開始監控，當有名額時立即通知並停止監控
每人限制監控十門課程

以下為指令使用教學
1.查詢及監控課程餘額
• 直接輸入課程編號(EX:7002)

2.查看目前監控課程
• 指令:清單

3.取消課程監控指令
• 取消單一課程：取消 課程編號
• 取消全部課程：取消 全部"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )
        return

    # View monitoring list
    if message == '清單':
        monitoring_list = get_user_monitoring_list(user_id)

        if not monitoring_list:
            response = """(目前沒有正在監控的課程)"""
        else:
            course_list = []
            for course_id, data in monitoring_list.items():
                course_list.append(f"• {data['course_name']} ({course_id})")

            courses_text = '\n'.join(course_list)
            response = f"""正在監控 {len(monitoring_list)} 個課程：
{courses_text}

(可以透過"幫助"來了解如何取消監控)"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
        return

    # Cancel monitoring
    if message.startswith('取消 '):
        target = message[3:].strip()

        if target == '全部':
            # Cancel all monitoring
            courses, count = stop_monitoring(user_id)

            if count > 0:
                course_list = []
                for course_data in courses:
                    course_list.append(f"• {course_data['course_name']}")

                courses_text = '\n'.join(course_list)
                response = f"""(已取消監控，可透過"清單"查詢目前的所有監控項目)

共取消 {count} 個課程：
{courses_text}"""
            else:
                response = """(目前沒有正在監控的課程)"""
        else:
            # Cancel single course monitoring
            course_id = target

            if not re.match(r'^\d{4}$', course_id):
                response = """課程編號格式錯誤

請使用正確的格式：
• 取消單一：取消 7002
• 取消全部：取消 全部"""

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response)
                )
                return

            course_name, count = stop_monitoring(user_id, course_id)

            if count > 0:
                response = f"""(已取消監控，可透過"清單"查詢目前的所有監控項目)

課程名稱：{course_name}
選課編號：{course_id}"""
            else:
                response = f"""課程未在監控清單中

選課編號：{course_id}

使用「清單」查看目前監控課程"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
        return

    # Direct course ID query (auto-monitoring)
    if re.match(r'^\d{4}$', message):
        # Query course
        result = query.query_course(message)

        if result and not result.get("error"):
            course_name = result['course_name']
            available = result['available']

            if available > 0:
                # Course has slots, display results
                formatted_result = query.format_result(result)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=formatted_result)
                )
            else:
                # Course has no slots, automatically start monitoring
                if start_monitoring(user_id, message, course_name):
                    response = f"""成功加入監控清單!
課程名稱：{course_name}
選課編號：{message}
科目代碼：{result['course_code']}
學分數：{result['credits']}
修課人數：{result['current_students']}/{result['max_students']}
剩餘名額：{available} 人
(目前沒有名額，當有名額時會由line主動通知)
(可透過"清單"查詢目前的所有監控項目)"""
                else:
                    response = f"""課程名稱：{course_name}
選課編號：{message}
科目代碼：{result['course_code']}
學分數：{result['credits']}
修課人數：{result['current_students']}/{result['max_students']}
剩餘名額：{available} 人
(課程已在監控清單中)"""

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=response)
                )
        else:
            error_msg = result.get("error", "Query failed") if result else "Query failed"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=error_msg)
            )
        return

    # Other messages show help
    help_text = """錯誤指令，請用"幫助"指令來了解如何命令機器人"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=help_text)
    )


if __name__ == "__main__":
    print("Starting course monitoring bot...")

    # Test login
    if query.login():
        print("System ready")
    else:
        print("Login failed, please check environment variable settings")

    print("Monitoring feature activated")
    app.run(host='0.0.0.0', port=5000, debug=True)