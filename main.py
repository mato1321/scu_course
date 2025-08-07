import os
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 載入環境變數
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
SOOCHOW_USERNAME = os.getenv('SOOCHOW_USERNAME')
SOOCHOW_PASSWORD = os.getenv('SOOCHOW_PASSWORD')

# 初始化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

class CourseQuery:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logged_in = False

    def login(self):
        """登入東吳校務系統"""
        try:
            # 取得登入頁面
            login_url = "https://web.sys.scu.edu.tw/logins.asp"
            self.session.get(login_url)

            # 提交登入資料
            login_data = {
                'id': SOOCHOW_USERNAME,
                'passwd': SOOCHOW_PASSWORD
            }

            submit_url = "https://web.sys.scu.edu.tw/login0.asp"
            response = self.session.post(submit_url, data=login_data)

            # 檢查登入結果
            content = response.content.decode('big5', errors='ignore')
            if "登入成功" in content:
                self.logged_in = True
                print("✅ 登入成功")
                return True
            else:
                print("❌ 登入失敗")
                return False

        except Exception as e:
            print(f"登入錯誤: {e}")
            return False

    def query_course(self, course_id):
        """查詢課程餘額"""
        if not self.logged_in:
            if not self.login():
                return "登入失敗，請檢查帳號密碼"

        try:
            print(f"🔍 查詢課程 {course_id}")

            # 先訪問查詢頁面
            query_page_url = "https://web.sys.scu.edu.tw/course201.asp"
            self.session.get(query_page_url)

            # 提交查詢到 course202.asp
            submit_url = "https://web.sys.scu.edu.tw/course202.asp"
            query_data = {
                'syear': '114',
                'smester': '1',
                'classid': course_id
            }

            print(f"📤 提交查詢資料: {query_data}")
            response = self.session.post(submit_url, data=query_data)
            content = response.content.decode('big5', errors='ignore')

            print(f"📥 收到回應，長度: {len(content)} 字元")

            # 解析結果
            return self.parse_result(content, course_id)

        except Exception as e:
            print(f"查詢錯誤: {e}")
            return f"查詢失敗：{e}"

    def parse_result(self, content, course_id):
        """解析查詢結果"""
        try:
            print(f"🔍 開始解析課程 {course_id}")

            # 檢查是否有錯誤訊息
            if "查無此課程" in content or "課程不存在" in content:
                return f"查無課程編號：{course_id}"

            # 檢查是否找到課程編號
            if course_id not in content:
                print(f"❌ 在回應中找不到課程編號 {course_id}")
                return f"在查詢結果中找不到課程 {course_id}"

            soup = BeautifulSoup(content, 'html.parser')

            # 找到包含課程資料的表格
            tables = soup.find_all('table')
            print(f"📋 找到 {len(tables)} 個表格")

            for table in tables:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    # 檢查每個欄位是否包含課程編號
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if course_id in cell_text:
                            print(f"✅ 找到包含課程編號的欄位: {cell_text}")

                            # 嘗試解析課程資訊
                            result = self.extract_course_info(cell_text, course_id)
                            if result:
                                return result

            return f"找到課程編號 {course_id} 但無法解析詳細資訊"

        except Exception as e:
            print(f"解析錯誤: {e}")
            return f"解析結果時發生錯誤：{e}"

    def extract_course_info(self, text, course_id):
        """提取課程資訊"""
        try:
            print(f"📄 解析文字: {text}")

            # 建立正則表達式模式
            pattern = course_id + r'([A-Z0-9]+)([^0-9]+)(\d+)'
            match = re.search(pattern, text)

            if match:
                course_code = match.group(1)
                course_name = match.group(2).strip()
                numbers = match.group(3)

                print(f"科目代碼: {course_code}")
                print(f"課程名稱: {course_name}")
                print(f"數字部分: {numbers}")

                # 解析數字部分
                credits, max_students, current_students = self.parse_numbers(numbers)
                available = max_students - current_students

                print(f"學分: {credits}, 上限: {max_students}, 目前: {current_students}, 剩餘: {available}")

                # 根據剩餘名額返回不同格式
                return self.format_result(course_name, course_id, course_code, credits,
                                        current_students, max_students, available)

            # 如果第一個正則表達式失敗，嘗試其他方法
            remaining_text = text[len(course_id):]

            # 尋找科目代碼
            code_match = re.search(r'^([A-Z0-9]{6,10})', remaining_text)
            if code_match:
                course_code = code_match.group(1)
                rest_text = remaining_text[len(course_code):]

                # 尋找最後的數字
                numbers_pattern = r'(\d+)$'
                numbers_match = re.search(numbers_pattern, rest_text)
                if numbers_match:
                    numbers = numbers_match.group(1)
                    course_name = rest_text[:rest_text.rfind(numbers)].strip()

                    credits, max_students, current_students = self.parse_numbers(numbers)
                    available = max_students - current_students

                    return self.format_result(course_name, course_id, course_code, credits,
                                            current_students, max_students, available)

            return None

        except Exception as e:
            print(f"提取課程資訊錯誤: {e}")
            return None

    def format_result(self, course_name, course_id, course_code, credits,
                     current_students, max_students, available):
        """格式化結果"""
        if available <= 0:
            # 沒有名額的格式
            result = f"""課程名稱：{course_name}
選課編號：{course_id}
科目代碼：{course_code}
學分數：{credits}
修課人數：{current_students}/{max_students}
剩餘名額：{available} 人
(目前沒有名額，當有名額時會由line主動通知)"""
        else:
            # 有名額的格式
            result = f"""課程名稱：{course_name}
選課編號：{course_id}
科目代碼：{course_code}
學分數：{credits}
修課人數：{current_students}/{max_students}
剩餘名額：{available} 人
(目前有{available}個名額，請盡快去加選!)"""

        return result

    def parse_numbers(self, numbers_str):
        """解析數字字串，提取學分、上限人數、目前人數"""
        try:
            if len(numbers_str) == 5:  # 例如: 36060
                credits = int(numbers_str[0])
                max_students = int(numbers_str[1:3])
                current_students = int(numbers_str[3:5])
            elif len(numbers_str) == 4:  # 例如: 3660
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

# 建立查詢物件
query = CourseQuery()

@app.route("/")
def home():
    return """
    <h1>🤖 東吳課程餘額查詢機器人</h1>
    <p>✅ 服務運行中</p>
    <p>💬 LINE訊息格式：直接輸入4位數課程編號</p>
    <p>📝 範例：7002</p>
    <p>🎯 功能：根據剩餘名額顯示不同提示訊息</p>
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
    message = event.message.text.strip()

    # 檢查是否為4位數字
    if re.match(r'^\d{4}$', message):
        # 查詢課程
        result = query.query_course(message)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    else:
        # 說明訊息
        help_text = """❓ 使用說明

💡 請直接輸入4位數課程編號查詢

📝 範例：
• 7002
• 3001
• 1234

🔢 格式：必須是4位數字

🎯 功能：
• 有名額：顯示"查詢成功"並提示盡快加選
• 沒名額：提示會自動通知"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )

if __name__ == "__main__":
    print("🚀 啟動課程查詢機器人...")

    # 測試登入
    if query.login():
        print("✅ 系統準備就緒")
    else:
        print("❌ 登入失敗，請檢查環境變數設定")

    app.run(host='0.0.0.0', port=5000, debug=True)