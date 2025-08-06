"""
東吳課程餘額監控機器人 (改進版)
- 查詢課程餘額
- 自動監控額滿課程
- 有名額時立即LINE通知
- 加強安全性和錯誤處理
- 優化資料庫連接和效能
"""

import os
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
import threading
import re
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask import Flask, request, abort

# ==================== 日誌設定 ====================

def setup_logging():
    """設定日誌系統"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'course_monitor.log')

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== 載入環境變數 ====================

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ 已載入 .env 檔案")
except ImportError:
    logger.warning("⚠️  python-dotenv 未安裝，使用系統環境變數")

# ==================== 自定義異常 ====================

class CourseMonitorError(Exception):
    """課程監控相關錯誤"""
    pass

class LoginError(CourseMonitorError):
    """登入錯誤"""
    pass

class NetworkError(CourseMonitorError):
    """網路錯誤"""
    pass

class ValidationError(CourseMonitorError):
    """輸入驗證錯誤"""
    pass

# ==================== 輸入驗證器 ====================

class InputValidator:
    """輸入驗證類別"""

    @staticmethod
    def validate_course_id(course_id):
        """驗證課程代碼格式"""
        if not course_id or not isinstance(course_id, str):
            raise ValidationError("課程代碼不能為空")

        if not re.match(r'^\d{4}$', course_id.strip()):
            raise ValidationError("課程代碼必須是4位數字")

        return course_id.strip()

    @staticmethod
    def validate_category(category):
        """驗證課程類別"""
        if not category or not isinstance(category, str):
            raise ValidationError("課程類別不能為空")

        category = category.strip()
        if category not in ['通識', '體育']:
            raise ValidationError(f"不支援的課程類別：{category}")

        return category

    @staticmethod
    def sanitize_input(text):
        """清理用戶輸入"""
        if not text:
            return ""
        return re.sub(r'[<>\"\'&]', '', str(text).strip())

# ==================== 資料庫管理器 ====================

class DatabaseManager:
    """資料庫管理類別"""

    def __init__(self, db_name):
        self.db_name = db_name
        self.lock = threading.Lock()
        self.init_database()

    @contextmanager
    def get_connection(self):
        """資料庫連接上下文管理器"""
        conn = None
        try:
            with self.lock:
                conn = sqlite3.connect(
                    self.db_name,
                    check_same_thread=False,
                    timeout=30
                )
                conn.row_factory = sqlite3.Row
                yield conn
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"資料庫操作錯誤: {e}")
            raise CourseMonitorError(f"資料庫操作失敗: {e}")
        finally:
            if conn:
                conn.close()

    def init_database(self):
        """初始化資料庫"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 監控表：儲存額滿的課程
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    course_name TEXT,
                    status TEXT DEFAULT 'full',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id, category)
                )
            ''')

            # 查詢歷史表：記錄所有查詢
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    course_name TEXT,
                    current_count INTEGER,
                    max_count INTEGER,
                    available INTEGER,
                    query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 系統日誌表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_level TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

        logger.info(f"✅ 資料庫初始化完成 ({self.db_name})")

# ==================== 設定區 ====================

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# 東吳校務系統帳號
SOOCHOW_USERNAME = os.getenv('SOOCHOW_USERNAME')
SOOCHOW_PASSWORD = os.getenv('SOOCHOW_PASSWORD')

# 監控設定
MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '5'))
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Web伺服器設定
PORT = int(os.getenv('PORT', '5000'))
HOST = os.getenv('HOST', '0.0.0.0')

# 資料庫設定
DATABASE_NAME = os.getenv('DATABASE_NAME', 'course_monitor.db')

# 系統設定
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
MAX_MONITORING_PER_USER = int(os.getenv('MAX_MONITORING_PER_USER', '10'))
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))

# 課程類別設定
COURSE_CATEGORIES = {
    '通識': '07:通識',
    '體育': '05:體育'
}

# ==================== 設定驗證 ====================

def validate_config():
    """驗證必要的環境變數"""
    required_vars = [
        ('LINE_CHANNEL_ACCESS_TOKEN', LINE_CHANNEL_ACCESS_TOKEN),
        ('LINE_CHANNEL_SECRET', LINE_CHANNEL_SECRET),
        ('SOOCHOW_USERNAME', SOOCHOW_USERNAME),
        ('SOOCHOW_PASSWORD', SOOCHOW_PASSWORD)
    ]

    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing_vars.append(var_name)

    if missing_vars:
        logger.error("❌ 缺少必要的環境變數:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        return False

    logger.info("✅ 環境變數驗證通過")
    return True

# ==================== 初始化 ====================

if not validate_config():
    logger.critical("❌ 設定驗證失敗，程式無法啟動")
    exit(1)

try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    app = Flask(__name__)
    db_manager = DatabaseManager(DATABASE_NAME)
    logger.info("✅ LINE Bot API 初始化完成")
except Exception as e:
    logger.critical(f"❌ 初始化失敗: {e}")
    exit(1)

# ==================== 速率限制 ====================

class RateLimiter:
    """簡單的速率限制器"""

    def __init__(self):
        self.requests = {}
        self.lock = threading.Lock()

    def is_allowed(self, user_id):
        """檢查是否允許請求"""
        now = datetime.now()
        with self.lock:
            if user_id not in self.requests:
                self.requests[user_id] = []

            # 清理舊請求
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < timedelta(minutes=1)
            ]

            # 檢查限制
            if len(self.requests[user_id]) >= RATE_LIMIT_PER_MINUTE:
                return False

            self.requests[user_id].append(now)
            return True

rate_limiter = RateLimiter()

# ==================== 核心監控類別 ====================

class CourseMonitor:
    """東吳課程監控器 (改進版)"""

    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.login_success = False
        self.last_login_time = None
        self.login_lock = threading.Lock()
        self.login_to_soochow()

    def setup_session(self):
        """設定HTTP會話"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })

    def login_to_soochow(self):
        """登入東吳校務系統（改進版）"""
        with self.login_lock:
            try:
                logger.info("🔐 正在登入東吳校務系統...")

                for attempt in range(MAX_RETRY_ATTEMPTS):
                    try:
                        # 取得登入頁面
                        login_url = "https://web.sys.scu.edu.tw/logins.asp"
                        response = self.session.get(login_url, timeout=REQUEST_TIMEOUT)

                        if response.status_code != 200:
                            raise NetworkError(f"無法存取登入頁面，狀態碼: {response.status_code}")

                        # 解析頁面內容
                        content = self.decode_content(response.content)
                        soup = BeautifulSoup(content, 'html.parser')

                        if not soup.find('form', {'name': 'LoginForm'}):
                            raise LoginError("找不到登入表單")

                        # 提交登入資料
                        login_data = {
                            'id': SOOCHOW_USERNAME,
                            'passwd': SOOCHOW_PASSWORD
                        }

                        submit_url = "https://web.sys.scu.edu.tw/login0.asp"
                        login_response = self.session.post(
                            submit_url,
                            data=login_data,
                            timeout=REQUEST_TIMEOUT
                        )

                        if login_response.status_code != 200:
                            raise NetworkError(f"登入請求失敗，狀態碼: {login_response.status_code}")

                        # 檢查登入結果
                        result_content = self.decode_content(login_response.content)

                        if "登入成功" in result_content and SOOCHOW_USERNAME in result_content:
                            self.login_success = True
                            self.last_login_time = datetime.now()
                            logger.info("✅ 東吳校務系統登入成功")
                            return True
                        else:
                            raise LoginError("登入失敗，請檢查帳號密碼")

                    except (requests.ConnectionError, requests.Timeout) as e:
                        logger.warning(f"⚠️ 登入嘗試 {attempt + 1}/{MAX_RETRY_ATTEMPTS} 失敗: {e}")
                        if attempt < MAX_RETRY_ATTEMPTS - 1:
                            time.sleep(2 ** attempt)  # 指數退避
                        else:
                            raise NetworkError("網路連線失敗，請稍後再試")

                raise LoginError("登入失敗，已達最大重試次數")

            except Exception as e:
                logger.error(f"❌ 登入時發生錯誤: {e}")
                self.login_success = False
                return False

    def check_login_status(self):
        """檢查登入狀態並在需要時重新登入"""
        if not self.login_success:
            return self.login_to_soochow()

        # 檢查是否需要重新登入（30分鐘後）
        if (self.last_login_time and
            datetime.now() - self.last_login_time > timedelta(minutes=30)):
            logger.info("🔄 登入逾時，重新登入...")
            return self.login_to_soochow()

        return True

    def decode_content(self, content):
        """解碼網頁內容"""
        encodings = ['big5', 'utf-8']
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode('utf-8', errors='ignore')

    # ==================== 課程查詢 ====================

    def query_course(self, course_id, category, user_id):
        """查詢課程餘額（改進版）"""
        try:
            # 驗證輸入
            course_id = InputValidator.validate_course_id(course_id)
            category = InputValidator.validate_category(category)

            # 檢查用戶監控數量限制
            self.check_user_monitoring_limit(user_id)

            # 檢查登入狀態
            if not self.check_login_status():
                return "LOGIN_FAILED"

            logger.info(f"🔍 查詢課程: {course_id} ({category})")

            # 取得課程查詢結果
            course_data = self.get_course_data(category)
            if not course_data:
                return "QUERY_FAILED"

            # 解析課程資料
            course_info = self.parse_course_data(course_data, course_id, category)

            if course_info:
                # 找到課程 = 有餘額
                logger.info(f"✅ 找到課程: {course_info['course_name']} (餘額: {course_info['available']})")
                self.save_query_history(user_id, course_info)
                self.remove_from_monitoring(user_id, course_id)
                return course_info
            else:
                # 沒找到課程 = 額滿
                logger.info(f"❌ 課程 {course_id} 額滿，加入監控")
                self.add_to_monitoring(user_id, course_id, category)
                return "FULL"

        except ValidationError as e:
            logger.warning(f"⚠️ 輸入驗證失敗: {e}")
            return f"VALIDATION_ERROR: {e}"
        except (NetworkError, LoginError) as e:
            logger.error(f"❌ 系統錯誤: {e}")
            return "SYSTEM_ERROR"
        except Exception as e:
            logger.error(f"❌ 查詢課程時發生未知錯誤: {e}")
            return "UNKNOWN_ERROR"

    def check_user_monitoring_limit(self, user_id):
        """檢查用戶監控數量限制"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) as count FROM monitoring WHERE user_id = ? AND status = "full"',
                (user_id,)
            )
            count = cursor.fetchone()['count']

            if count >= MAX_MONITORING_PER_USER:
                raise ValidationError(f"監控數量已達上限（{MAX_MONITORING_PER_USER}門）")

    def get_course_data(self, category):
        """取得指定類別的課程資料（改進版）"""
        try:
            for attempt in range(MAX_RETRY_ATTEMPTS):
                try:
                    # 步驟1：訪問查詢頁面
                    query_page_url = "https://web.sys.scu.edu.tw/course10.asp"
                    self.session.get(query_page_url, timeout=REQUEST_TIMEOUT)

                    # 步驟2：提交查詢請求
                    course_param = COURSE_CATEGORIES.get(category)
                    query_data = {
                        'syear': '114',
                        'smester': '1',
                        'cour': course_param
                    }

                    # 方法1：向course11.asp提交
                    query_url = "https://web.sys.scu.edu.tw/course11.asp"
                    response = self.session.post(
                        query_url,
                        data=query_data,
                        timeout=REQUEST_TIMEOUT
                    )

                    if response.status_code == 200:
                        content = self.decode_content(response.content)
                        if self.is_valid_course_data(content):
                            return content

                    # 方法2：向course10.asp提交（備用）
                    query_data['Submit'] = '查詢'
                    response = self.session.post(
                        query_page_url,
                        data=query_data,
                        timeout=REQUEST_TIMEOUT
                    )

                    if response.status_code == 200:
                        content = self.decode_content(response.content)
                        if self.is_valid_course_data(content):
                            return content

                except (requests.ConnectionError, requests.Timeout) as e:
                    logger.warning(f"⚠️ 取得課程資料嘗試 {attempt + 1}/{MAX_RETRY_ATTEMPTS} 失敗: {e}")
                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        time.sleep(1)

            raise NetworkError("無法取得課程資料")

        except Exception as e:
            logger.error(f"❌ 取得課程資料時發生錯誤: {e}")
            return None

    def is_valid_course_data(self, content):
        """檢查是否為有效的課程資料"""
        if not content:
            return False

        indicators = [
            '<TABLE BORDER=1>',
            '<table border="1">',
            '選課編號',
            '科目代碼'
        ]
        return any(indicator in content for indicator in indicators)

    def parse_course_data(self, content, target_course_id, category):
        """解析課程資料（改進版）"""
        if not content or target_course_id not in content:
            return None

        try:
            # 定義正則表達式模式
            patterns = [
                # 模式1：完整格式
                r'<TD align=center>(\d{4})<TD><a[^>]+>([^<]+)</a><TD><A[^>]+>([^<]+)&nbsp;&nbsp;&nbsp;&nbsp;</a><TD align=center>(\d+)<TD align=center>(\d+)<TD align=center>(\d+)<TD align=center>([^<]+)',
                # 模式2：簡化格式
                r'<TD align=center>(\d{4})<TD><a[^>]+>([^<]+)</a><TD><A[^>]+>([^<]*)</a><TD align=center>(\d+)<TD align=center>(\d+)<TD align=center>(\d+)<TD align=center>([^<]+)'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    course_info = self.find_target_course(matches, target_course_id, category)
                    if course_info:
                        return course_info

            return None

        except Exception as e:
            logger.error(f"❌ 解析課程資料時發生錯誤: {e}")
            return None

    def find_target_course(self, matches, target_course_id, category):
        """在匹配結果中尋找目標課程"""
        for match in matches:
            try:
                course_number = match[0]
                if course_number == target_course_id:
                    return self.create_course_info(match, target_course_id, category)
            except Exception as e:
                logger.warning(f"⚠️ 解析課程資料時發生錯誤: {e}")
                continue
        return None

    def create_course_info(self, match, course_id, category):
        """建立課程資訊物件"""
        try:
            course_number = match[0]
            course_code = match[1]
            raw_course_name = match[2]
            credits = match[3]
            max_count = int(match[4]) if match[4].isdigit() else 0
            current_count = int(match[5]) if match[5].isdigit() else 0
            class_info = match[6] if len(match) > 6 else "未知"

            # 清理課程名稱
            course_name = self.clean_course_name(raw_course_name)
            available = max(0, max_count - current_count)

            return {
                'course_id': course_id,
                'course_number': course_number,
                'course_code': course_code,
                'course_name': course_name,
                'current_count': current_count,
                'max_count': max_count,
                'available': available,
                'credits': credits,
                'category': category,
                'class_info': class_info
            }
        except Exception as e:
            logger.error(f"❌ 建立課程資訊時發生錯誤: {e}")
            return None

    def clean_course_name(self, raw_name):
        """清理課程名稱"""
        if not raw_name:
            return "未知課程"

        # 移除HTML實體
        cleaned = raw_name.replace('&nbsp;', '').replace('&amp;', '&')
        cleaned = cleaned.replace('&lt;', '<').replace('&gt;', '>')
        cleaned = cleaned.replace('&quot;', '"')
        # 移除多餘空格
        return re.sub(r'\s+', ' ', cleaned.strip())

    # ==================== 監控管理 ====================

    def add_to_monitoring(self, user_id, course_id, category):
        """將額滿課程加入監控"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO monitoring 
                    (user_id, course_id, category, course_name, status, created_at, last_check)
                    VALUES (?, ?, ?, ?, 'full', ?, ?)
                ''', (user_id, course_id, category, f"{category}課程-{course_id}",
                      datetime.now(), datetime.now()))

            logger.info(f"📋 已將 {course_id} ({category}) 加入監控")

        except Exception as e:
            logger.error(f"❌ 加入監控時發生錯誤: {e}")
            raise CourseMonitorError(f"加入監控失敗: {e}")

    def remove_from_monitoring(self, user_id, course_id=None):
        """移除監控"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                if course_id:
                    cursor.execute(
                        'DELETE FROM monitoring WHERE user_id = ? AND course_id = ?',
                        (user_id, course_id)
                    )
                    removed_count = cursor.rowcount
                    logger.info(f"📋 已移除 {course_id} 的監控")
                else:
                    cursor.execute(
                        'SELECT COUNT(*) as count FROM monitoring WHERE user_id = ?',
                        (user_id,)
                    )
                    removed_count = cursor.fetchone()['count']
                    cursor.execute('DELETE FROM monitoring WHERE user_id = ?', (user_id,))
                    logger.info(f"📋 已移除用戶 {user_id} 的所有監控")

                return removed_count

        except Exception as e:
            logger.error(f"❌ 移除監控時發生錯誤: {e}")
            return 0

    def get_monitoring_courses(self):
        """取得所有監控中的課程"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT user_id, course_id, category, course_name FROM monitoring WHERE status = "full"'
                )
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"❌ 取得監控課程時發生錯誤: {e}")
            return []

    def get_user_monitoring(self, user_id):
        """取得用戶的監控清單"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT course_id, category, course_name, created_at 
                    FROM monitoring 
                    WHERE user_id = ? AND status = "full"
                    ORDER BY created_at DESC
                ''', (user_id,))
                return cursor.fetchall()

        except Exception as e:
            logger.error(f"❌ 取得用戶監控清單時發生錯誤: {e}")
            return []

    # ==================== 背景監控 ====================

    def start_monitoring(self):
        """啟動背景監控"""
        logger.info(f"⏰ 啟動課程監控（每{MONITOR_INTERVAL}秒檢查一次）")

        while True:
            try:
                self.check_monitored_courses()
                time.sleep(MONITOR_INTERVAL)
            except Exception as e:
                logger.error(f"❌ 監控過程中發生錯誤: {e}")
                time.sleep(MONITOR_INTERVAL)

    def check_monitored_courses(self):
        """檢查所有監控中的課程"""
        if not self.check_login_status():
            logger.warning("⚠️ 登入狀態異常，跳過監控檢查")
            return

        courses = self.get_monitoring_courses()
        if not courses:
            return

        logger.info(f"🔍 檢查 {len(courses)} 門監控課程...")

        for course_row in courses:
            try:
                user_id = course_row['user_id']
                course_id = course_row['course_id']
                category = course_row['category']
                course_name = course_row['course_name']

                # 查詢課程是否有名額
                course_data = self.get_course_data(category)
                if course_data:
                    course_info = self.parse_course_data(course_data, course_id, category)

                    if course_info:
                        # 有名額了！發送通知
                        logger.info(f"🎉 {course_id} 有名額了！")
                        self.send_notification(user_id, course_info)
                        self.remove_from_monitoring(user_id, course_id)
                        self.save_query_history(user_id, course_info)

                time.sleep(0.5)  # 避免請求過快

            except Exception as e:
                logger.error(f"❌ 檢查課程 {course_id} 時發生錯誤: {e}")

        # 更新檢查時間
        self.update_check_time()

    def update_check_time(self):
        """更新最後檢查時間"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE monitoring SET last_check = ? WHERE status = "full"',
                    (datetime.now(),)
                )

        except Exception as e:
            logger.error(f"❌ 更新檢查時間時發生錯誤: {e}")

    def send_notification(self, user_id, course_info):
        """發送LINE通知"""
        message = f"""🎉 好消息！課程有名額了！

📚 課程：{course_info['course_name']}
📋 類別：{course_info['category']}
🔢 選課編號：{course_info['course_number']}
📝 科目代碼：{course_info['course_code']}
👥 目前人數：{course_info['current_count']}/{course_info['max_count']}
✅ 可用名額：{course_info['available']} 人
🏫 開課班級：{course_info['class_info']}

⚡ 快去選課吧！

🤖 已自動從監控清單移除此課程"""

        try:
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            logger.info(f"✅ 已發送通知給用戶 {user_id}")
        except LineBotApiError as e:
            logger.error(f"❌ 發送LINE通知時發生錯誤: {e}")
        except Exception as e:
            logger.error(f"❌ 發送通知時發生未知錯誤: {e}")

    # ==================== 資料記錄 ====================

    def save_query_history(self, user_id, course_info):
        """儲存查詢歷史"""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO query_history 
                    (user_id, course_id, category, course_name, current_count, max_count, available, query_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, course_info['course_id'], course_info['category'],
                    course_info['course_name'], course_info['current_count'],
                    course_info['max_count'], course_info['available'], datetime.now()
                ))

        except Exception as e:
            logger.error(f"❌ 儲存查詢歷史時發生錯誤: {e}")

    def cleanup_old_records(self):
        """清理舊資料"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)

            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM query_history WHERE query_time < ?',
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(f"🧹 已清理 {deleted_count} 筆舊記錄")

        except Exception as e:
            logger.error(f"❌ 清理舊記錄時發生錯誤: {e}")


# ==================== 初始化監控器 ====================

monitor = CourseMonitor()

# ==================== Web應用 ====================

@app.route("/", methods=['GET'])
def home():
    """首頁"""
    try:
        monitoring_count = len(monitor.get_monitoring_courses()) if monitor.login_success else 0

        return f"""
        <h1>🤖 東吳課程餘額監控機器人 (改進版)</h1>
        <p>✅ 伺服器運行中</p>
        <p>🔑 登入狀態: {'✅ 成功' if monitor.login_success else '❌ 失敗'}</p>
        <p>📋 監控課程數: {monitoring_count} 門</p>
        <p>🔄 監控頻率: 每{MONITOR_INTERVAL}秒</p>
        <p>👥 單用戶監控上限: {MAX_MONITORING_PER_USER} 門</p>
        <p>⚡ 速率限制: {RATE_LIMIT_PER_MINUTE} 次/分鐘</p>
        
        <h2>💬 支援指令</h2>
        <ul>
            <li><code>[類別] [課程代碼]</code> - 查詢課程餘額</li>
            <li><code>清單</code> - 查看監控的課程</li>
            <li><code>取消 [課程代碼]</code> - 取消監控</li>
            <li><code>取消 全部</code> - 取消所有監控</li>
            <li><code>測試</code> - 檢查機器人狀態</li>
        </ul>
        
        <h2>📋 支援類別</h2>
        <ul>
            <li>體育</li>
            <li>通識</li>
        </ul>
        
        <h2>💡 使用說明</h2>
        <p>📱 用LINE加入機器人好友後：</p>
        <ol>
            <li>輸入 <code>體育 7002</code> 查詢課程</li>
            <li>有餘額會顯示詳細資訊</li>
            <li>額滿會自動加入監控</li>
            <li>有名額時會立即通知</li>
        </ol>
        
        <h2>🔧 改進功能</h2>
        <ul>
            <li>✅ 加強錯誤處理和重試機制</li>
            <li>✅ 輸入驗證和安全性提升</li>
            <li>✅ 資料庫連接池優化</li>
            <li>✅ 速率限制和用戶監控上限</li>
            <li>✅ 完整的日誌記錄</li>
            <li>✅ 自動登入狀態檢查</li>
        </ul>
        """
    except Exception as e:
        logger.error(f"❌ 首頁載入錯誤: {e}")
        return "❌ 系統暫時無法使用，請稍後再試"

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("❌ LINE Webhook簽名驗證失敗")
        abort(400)
    except Exception as e:
        logger.error(f"❌ Webhook處理錯誤: {e}")
        abort(500)

    return 'OK'

@app.route("/health", methods=['GET'])
def health_check():
    """健康檢查端點"""
    try:
        status = {
            'status': 'healthy' if monitor.login_success else 'degraded',
            'login_status': monitor.login_success,
            'monitoring_count': len(monitor.get_monitoring_courses()),
            'last_login_time': monitor.last_login_time.isoformat() if monitor.last_login_time else None,
            'timestamp': datetime.now().isoformat()
        }
        return status
    except Exception as e:
        logger.error(f"❌ 健康檢查錯誤: {e}")
        return {'status': 'error', 'message': str(e)}, 500

# ==================== LINE訊息處理 ====================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理LINE訊息"""
    user_id = event.source.user_id
    message = InputValidator.sanitize_input(event.message.text)

    logger.info(f"📨 收到訊息: {message} (用戶: {user_id})")

    # 檢查速率限制
    if not rate_limiter.is_allowed(user_id):
        reply_text = f"⚠️ 請求過於頻繁，請稍後再試\n\n💡 限制：每分鐘最多 {RATE_LIMIT_PER_MINUTE} 次請求"
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        except Exception as e:
            logger.error(f"❌ 回覆速率限制訊息失敗: {e}")
        return

    try:
        reply_text = process_message(message, user_id)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

    except Exception as e:
        logger.error(f"❌ 處理訊息時發生錯誤: {e}")
        error_message = "❌ 處理請求時發生錯誤，請稍後再試"
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
        except Exception as reply_error:
            logger.error(f"❌ 回覆錯誤訊息失敗: {reply_error}")

def process_message(message, user_id):
    """處理訊息邏輯"""

    # 取消監控
    if message.startswith('取消'):
        return handle_cancel_monitoring(message, user_id)

    # 查看監控清單
    elif message == '清單':
        return handle_show_monitoring(user_id)

    # 測試狀態
    elif message == '測試':
        return handle_test_status()

    # 查詢課程
    else:
        parts = message.split()
        if len(parts) == 2:
            category, course_id = parts[0], parts[1]
            return handle_course_query(category, course_id, user_id)
        else:
            return get_help_message()

def handle_cancel_monitoring(message, user_id):
    """處理取消監控"""
    try:
        parts = message.split()

        if len(parts) >= 2:
            if parts[1] == '全部':
                count = monitor.remove_from_monitoring(user_id)
                return f"✅ 已取消監控所有課程，共 {count} 門課程" if count > 0 else "📋 您目前沒有任何監控"
            else:
                course_id = InputValidator.validate_course_id(parts[1])
                count = monitor.remove_from_monitoring(user_id, course_id)
                return f"✅ 已取消監控課程：{course_id}" if count > 0 else f"❌ 找不到監控的課程：{course_id}"
        else:
            return "❌ 請使用：取消 [課程代碼] 或 取消 全部"

    except ValidationError as e:
        return f"❌ {e}"
    except Exception as e:
        logger.error(f"❌ 處理取消監控時發生錯誤: {e}")
        return "❌ 取消監控時發生錯誤，請稍後再試"

def handle_show_monitoring(user_id):
    """處理查看監控清單"""
    try:
        courses = monitor.get_user_monitoring(user_id)

        if courses:
            reply_text = f"📋 您的監控清單（{len(courses)}/{MAX_MONITORING_PER_USER}）：\n\n"
            for i, course_row in enumerate(courses, 1):
                course_id = course_row['course_id']
                category = course_row['category']
                course_name = course_row['course_name']
                created_at = course_row['created_at']

                display_name = course_name[:25] + "..." if course_name and len(course_name) > 25 else (course_name or f"{category}課程")
                reply_text += f"{i}. {display_name}\n  📋 {category} - {course_id}\n  🕒 {created_at[:16]}\n\n"

            reply_text += f"💡 使用「取消 [課程代碼]」可移除監控"
            return reply_text
        else:
            return f"📋 您目前沒有監控任何課程\n\n💡 監控上限：{MAX_MONITORING_PER_USER} 門課程"

    except Exception as e:
        logger.error(f"❌ 處理監控清單時發生錯誤: {e}")
        return "❌ 取得監控清單時發生錯誤，請稍後再試"

def handle_test_status():
    """處理測試狀態"""
    try:
        status = "✅ 正常" if monitor.login_success else "❌ 登入失敗"
        monitoring_count = len(monitor.get_monitoring_courses())
        last_login = monitor.last_login_time.strftime('%H:%M:%S') if monitor.last_login_time else "未知"

        return f"""🤖 機器人狀態檢查

🔧 系統狀態：正常運行
🔑 登入狀態：{status}
🕒 上次登入：{last_login}
📊 監控功能：啟用
📋 總監控數：{monitoring_count} 門
🔄 檢查頻率：每{MONITOR_INTERVAL}秒
👥 監控上限：{MAX_MONITORING_PER_USER} 門/用戶
⚡ 速率限制：{RATE_LIMIT_PER_MINUTE} 次/分鐘

💡 系統運行正常"""

    except Exception as e:
        logger.error(f"❌ 處理測試狀態時發生錯誤: {e}")
        return "❌ 取得系統狀態時發生錯誤"

def handle_course_query(category, course_id, user_id):
    """處理課程查詢"""
    try:
        # 查詢課程
        result = monitor.query_course(course_id, category, user_id)

        if isinstance(result, dict):
            # 找到課程且有餘額
            return f"""✅ 查詢成功！

📚 課程：{result['course_name']}
📋 類別：{category}
🔢 選課編號：{result['course_number']}
📝 科目代碼：{result['course_code']}
👥 目前人數：{result['current_count']}/{result['max_count']}
✅ 可用名額：{result['available']} 人
🏫 開課班級：{result['class_info']}

💡 課程目前有名額可以選課！"""

        elif result == "FULL":
            # 課程額滿
            user_monitoring = monitor.get_user_monitoring(user_id)
            return f"""❌ 課程目前額滿

📋 課程代碼：{course_id} ({category})
🔒 狀態：額滿（未在餘額清單中）

🤖 已自動加入監控清單
🔔 一旦有名額會立即通知您
⏰ 每{MONITOR_INTERVAL}秒檢查一次

📊 您的監控數：{len(user_monitoring)}/{MAX_MONITORING_PER_USER}

💡 使用「清單」查看所有監控中的課程"""

        elif result.startswith("VALIDATION_ERROR"):
            # 驗證錯誤
            error_msg = result.split(": ", 1)[1] if ": " in result else "輸入格式錯誤"
            return f"""❌ {error_msg}

📋 支援的類別：體育、通識
🔢 課程代碼：4位數字

💡 正確格式：[類別] [課程代碼]
📝 範例：體育 7002"""

        elif result == "LOGIN_FAILED":
            # 登入失敗
            return f"""❌ 系統登入失敗

🔧 可能原因：
• 東吳校務系統維護中
• 網路連線問題
• 帳號密碼設定問題

💡 請稍後再試或聯繫管理員"""

        else:
            # 其他錯誤
            return f"""❌ 查詢失敗

📋 課程代碼：{course_id} ({category})
🔧 可能原因：網路問題或系統繁忙

💡 請稍後再試"""

    except Exception as e:
        logger.error(f"❌ 處理課程查詢時發生錯誤: {e}")
        return "❌ 查詢課程時發生錯誤，請稍後再試"

def get_help_message():
    """取得幫助訊息"""
    return f"""❓ 指令格式錯誤

💡 使用方式：[類別] [課程代碼]

📝 範例：
• 體育 7002 - 查詢體育課程
• 通識 3001 - 查詢通識課程

📌 其他指令：
• 清單 - 查看監控的課程
• 取消 [課程代碼] - 取消監控
• 取消 全部 - 取消所有監控
• 測試 - 檢查機器人狀態

⚙️ 系統限制：
• ⏰ 監控頻率：每{MONITOR_INTERVAL}秒檢查一次
• 👥 監控上限：{MAX_MONITORING_PER_USER} 門課程/用戶
• ⚡ 速率限制：{RATE_LIMIT_PER_MINUTE} 次請求/分鐘"""


# ==================== 主程式 ====================

def main():
    """主程式"""
    logger.info("🚀 啟動東吳課程餘額監控機器人 (改進版)")
    logger.info("=" * 60)

    # 檢查登入狀態
    if monitor.login_success:
        logger.info("✅ 系統初始化完成")
        logger.info(f"🔑 東吳系統：登入成功")
        logger.info(f"📋 課程類別：{', '.join(COURSE_CATEGORIES.keys())}")
        logger.info(f"⏰ 監控間隔：每{MONITOR_INTERVAL}秒")
        logger.info(f"👥 監控上限：{MAX_MONITORING_PER_USER} 門/用戶")
        logger.info(f"⚡ 速率限制：{RATE_LIMIT_PER_MINUTE} 次/分鐘")
    else:
        logger.warning("❌ 東吳系統登入失敗")
        logger.warning("⚠️  機器人將以受限模式運行")

    logger.info("=" * 60)

    # 啟動背景監控
    logger.info("🔄 啟動背景監控...")
    monitor_thread = threading.Thread(target=monitor.start_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()

    # 啟動定期清理任務
    def periodic_cleanup():
        while True:
            try:
                time.sleep(3600)  # 每小時執行一次
                monitor.cleanup_old_records()
            except Exception as e:
                logger.error(f"❌ 定期清理任務錯誤: {e}")

    cleanup_thread = threading.Thread(target=periodic_cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    # 啟動Web伺服器
    logger.info(f"🌐 啟動Web伺服器 ({HOST}:{PORT})")
    logger.info(f"📱 LINE Webhook準備就緒")
    logger.info(f"📊 資料庫檔案：{DATABASE_NAME}")
    logger.info(f"📝 日誌檔案：{os.getenv('LOG_FILE', 'course_monitor.log')}")
    if DEBUG_MODE:
        logger.info("🔧 除錯模式：啟用")
    logger.info("=" * 60)
    logger.info("✅ 機器人已啟動，等待訊息...")

    try:
        app.run(host=HOST, port=PORT, debug=DEBUG_MODE)
    except KeyboardInterrupt:
        logger.info("\n👋 機器人已停止運行")
    except Exception as e:
        logger.critical(f"❌ 伺服器發生嚴重錯誤: {e}")
        raise


if __name__ == "__main__":
    main()