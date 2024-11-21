import requests
import json
import time
from datetime import datetime
import logging
import base64
import random
import cv2
import numpy as np
from PIL import Image
import io
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

class TicketBot:
    def __init__(self):
        """初始化TicketBot"""
        # 确保日志目录存在
        log_dir = 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('log/ticket_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("="*50)
        self.logger.info("初始化 TicketBot...")
        self.logger.info("="*50)
        
        self.session = requests.Session()
        # 禁用SSL证书验证
        self.session.verify = False
        # 禁用SSL警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.base_url = "https://rce.tencentrio.com/sstmticket/sam"
        self.headers = {
            "Host": "rce.tencentrio.com",
            "Connection": "keep-alive",
            "mpsessid": "1AC6E75AF592E04CEBB5C178E55F4ABB4E3F124010A7AA9036F30191B2E06E595D000213AF7F7230@f5786a6a",
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN",
            "Referer": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html"
        }
        
        self.stadium_id = "69001"
        self.schedule_id = "61038"
        
        # 更新初始token
        self.qq_token = "S8r4Yx0kU93JOM8/TOykIaP3jKxyWKo3sJ7ktOj1/QKXvVCg2xKe09bDiO9r5Ogx6GCLEw=="
        
        # 初始化验证码相关参数
        self.captcha_app_id = "2013697930"
        self.captcha_sid = None
        
        # 验证登录状态
        if not self.check_login_status():
            self.logger.warning("登录状态无效，尝试刷新登录...")
            if not self.refresh_login():
                self.logger.error("登录状态刷新失败")
                raise Exception("登录状态无效")
        
        # 预热风控token
        self.logger.info("预热风控token...")
        self.get_qq_security_token()
        
        self.driver = webdriver.Chrome()  # 或其他浏览器
        self.wait = WebDriverWait(self.driver, 10)
        self.max_retries = 3  # 最大重试次数

    def get_available_dates(self):
        """获取可预订日期列表"""
        self.logger.info("-"*30)
        self.logger.info("正在获取可预订日期...")
        url = f"{self.base_url}/vendor/reserve/getReservedateListByStadiumId.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "sstCode": "ssmtifri",
            "appId": "wx1d7ddce169710ba7"
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            data = response.json()
            if data.get('success'):
                date_list = data.get('data', {}).get('resultList', [])
                available_dates = {}
                
                for date_info in date_list:
                    date = date_info['reservedate']
                    # 获取该日期的具体余票信息
                    period_info = self.get_period_list(date)
                    if period_info and period_info.get('success'):
                        periods = period_info['data']['reservePeriodList']
                        
                        morning_info = next((p for p in periods if p['starttime'].endswith('09:30:00')), None)
                        afternoon_info = next((p for p in periods if p['starttime'].endswith('12:30:00')), None)
                        
                        morning_tickets = morning_info['avaiablenum'] if morning_info else 0
                        afternoon_tickets = afternoon_info['avaiablenum'] if afternoon_info else 0
                        
                        if morning_tickets > 0 or afternoon_tickets > 0:
                            available_dates[date] = {
                                'total': morning_tickets + afternoon_tickets,
                                'morning': {
                                    'tickets': morning_tickets,
                                    'period_id': morning_info['id'] if morning_info else None,
                                    'time': '09:30-12:30'
                                },
                                'afternoon': {
                                    'tickets': afternoon_tickets,
                                    'period_id': afternoon_info['id'] if afternoon_info else None,
                                    'time': '12:30-15:00'
                                }
                            }
                            
                            self.logger.info(f"\n日期: {date}")
                            if available_dates[date]['morning']['tickets'] > 0:
                                self.logger.info(
                                    f"  上午场 ({available_dates[date]['morning']['time']}): "
                                    f"{available_dates[date]['morning']['tickets']}张"
                                )
                            if available_dates[date]['afternoon']['tickets'] > 0:
                                self.logger.info(
                                    f"  下午场 ({available_dates[date]['afternoon']['time']}): "
                                    f"{available_dates[date]['afternoon']['tickets']}张"
                                )
                
                return available_dates
            else:
                self.logger.error(f"获取可预订日期失败: {data.get('msg')}")
                return None
            
        except Exception as e:
            self.logger.error(f"获取可预订日期时发生错误: {str(e)}")
            return None

    def get_period_list(self, date):
        """获取指定日期的时间段余票信息"""
        url = f"{self.base_url}/vendor/reserve/getReservePeriodListByDate.xhtml"
        data = {
            "stadiumId": self.stadium_id,
            "reservedate": date,
            "sstCode": "ssmtifri",
            "appId": "wx1d7ddce169710ba7"
        }
        
        try:
            response = self.session.post(url, data=data, headers=self.headers)
            if response.status_code != 200:
                self.logger.error(f"获取时间段失败: HTTP {response.status_code}")
                return None
            
            result = response.json()
            if not result.get('success'):
                self.logger.error(f"获取时间段失败: {result.get('msg')}")
                return None
            
            return result
        
        except Exception as e:
            self.logger.error(f"获取时间段时发生错误: {str(e)}")
            return None

    def check_visitor_days(self):
        """获取预约访问配置并检查是否可以预约"""
        url = f"{self.base_url}/vendor/reserve/getReserveVisitorDaysAndOpenMinutesByStadiumId.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            
            # 添加状态码检查
            if response.status_code != 200:
                self.logger.error(f"HTTP错误: {response.status_code}")
                self.logger.error(f"响应内容: {response.text}")
                return None
            
            # 添加响应内容类型检查
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type.lower():
                self.logger.error(f"非JSON响应: {content_type}")
                self.logger.error(f"响应内: {response.text}")
                return None
            
            # 尝试解析JSON
            try:
                data = response.json()
                self.logger.info(f"Visitor Days Response: {data}")
                
                if data.get('success'):
                    open_buy_time = data['data']['openBuyTime']
                    current_time = int(time.time() * 1000)
                    
                    if current_time < open_buy_time:
                        wait_time = (open_buy_time - current_time) / 1000
                        self.logger.info(f"预约未开始，等待 {wait_time:.2f} 秒...")
                        if wait_time > 0:
                            time.sleep(wait_time)
                            # 重新获取配置
                            return self.check_visitor_days()
                    
                return data
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析错误: {str(e)}")
                self.logger.error(f"响应内容: {response.text}")
                return None
            
        except Exception as e:
            self.logger.error(f"获取预约配置失败: {str(e)}")
            self.logger.error(f"错误类型: {type(e)}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None

    def check_captcha_require(self):
        """检查是否需要验证码"""
        url = f"{self.base_url}/vendor/member/captchaRequire.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            return response.json()
        except Exception as e:
            self.logger.error(f"检查验证码要求失败: {str(e)}")
            return None

    def get_server_time(self):
        """取服务器时间"""
        url = f"{self.base_url}/vendor/common/getServerTime.xhtml"
        params = {
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            self.logger.debug(f"服务器时间响应: {response.text}")
            # 自动跳过验证码输入
            self.logger.info("自动跳过验证输入...")
            return response.json()
        except Exception as e:
            self.logger.error(f"获取服务器时间失败: {str(e)}")
            return None

    def get_risk_open(self):
        """检查风险控制状态"""
        url = f"{self.base_url}/vendor/member/getRiskOpen.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "orderType": "ticket2",
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            print(f"Risk Open Response: {response.text}")
            return response.json()
        except Exception as e:
            print(f"检查风险控制状态时发生错误: {str(e)}")
            return None

    def get_member_info(self):
        """获取会员信息"""
        url = f"{self.base_url}/vendor/member/memberInfo.xhtml"
        params = {
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            print(f"Member Info Response: {response.text}")
            return response.json()
        except Exception as e:
            print(f"获取会员信时发生错误: {str(e)}")
            return None

    def check_captcha(self, ticket):
        """验证码验证"""
        url = f"{self.base_url}/vendor/member/checkCaptcha.xhtml"
        params = {
            "ticket": ticket,
            "stadiumId": self.stadium_id,
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            print(f"Captcha Check Response: {response.text}")
            return response.json()
        except Exception as e:
            print(f"验证码验证时发生错误: {str(e)}")
            return None

    def get_payment_gateway_list(self):
        """获取支付网关列表"""
        url = f"{self.base_url}/vendor/member/getPaymentGatewayList.xhtml"
        params = {
            "platform": "APP",
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            print(f"Payment Gateway Response: {response.text}")
            return response.json()
        except Exception as e:
            print(f"获取支付网列表发生错误: {str(e)}")
            return None

    def calculate_slide_distance(self, target_img, template_img):
        """计算滑块需要移动的距离"""
        try:
            # 转换图片格式
            target = cv2.imdecode(np.frombuffer(target_img, np.uint8), cv2.IMREAD_COLOR)
            template = cv2.imdecode(np.frombuffer(template_img, np.uint8), cv2.IMREAD_COLOR)
            
            # 转换为灰度图
            target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # 模板匹配
            result = cv2.matchTemplate(target_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 获取匹配位置的X坐标
            x = max_loc[0]
            
            self.logger.info(f"计算得到的滑动距离: {x}px")
            return x
            
        except Exception as e:
            self.logger.error(f"计算滑动距离失败: {str(e)}")
            return None

    def simulate_slide_track(self, distance):
        """生成仿真的滑动轨迹"""
        tracks = []
        current = 0
        mid = distance * 3 / 4
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            tracks.append(round(move))
        
        return tracks

    def handle_captcha(self):
        """处理验证码的入口方法"""
        retries = self.max_retries
        while retries > 0:
            try:
                if self.handle_captcha_with_retry():
                    return True
                    
                retries -= 1
                self.logger.info(f"验证失败，还有 {retries} 次重试机会")
                
                if retries > 0:
                    time.sleep(2)  # 重试前等待
                    
            except Exception as e:
                self.logger.error(f"验证码处理出错: {str(e)}")
                retries -= 1
                
        self.logger.error("验证码处理失败")
        return False

    def handle_captcha_with_retry(self):
        """处理验证码(带重试)"""
        try:
            # 1. 先获取验证码初始化参数
            data = {
                "Action": "CheckCaptchaAppId",
                "CaptchaAppId": 2013697930  # 使用你的 AppId
            }
            response = self.session.post("https://m.captcha.qq.com/", json=data)
            result = response.json()
            
            if result.get("Response", {}).get("CaptchaCode") != 0:
                self.logger.error(f"验证码初始化失败: {result}")
                return False
                
            # 2. 使用 Selenium 处理滑块
            return self._handle_slider_captcha()
            
        except Exception as e:
            self.logger.error(f"验证码处理失败: {str(e)}")
            return False

    def _handle_slider_captcha(self):
        """处理滑块验证码"""
        try:
            # 等待验证码 iframe 加载
            iframe = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src,'m.captcha.qq.com')]"))
            )
            self.driver.switch_to.frame(iframe)
            
            # 等待滑块和背景图加载
            slider = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "tc-drag-thumb"))
            )
            bg_img = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "tc-bg-img"))
            )
            
            # 计算滑动距离
            distance = self._calculate_gap(bg_img)
            if not distance:
                return False
                
            # 生成滑动轨迹
            track = self._generate_track(distance)
            
            # 执行滑动
            success = self._do_slide(slider, track)
            
            return success
            
        except Exception as e:
            self.logger.error(f"滑块验证失败: {str(e)}")
            return False
        finally:
            # 切回主框架
            try:
                self.driver.switch_to.default_content()
            except:
                pass

    def _calculate_gap(self, bg_img):
        """计算缺口位置"""
        try:
            # 获取背景图
            bg_url = bg_img.get_attribute('src')
            bg_data = self.session.get(bg_url).content
            
            # 使用 OpenCV 处理图片
            img = cv2.imdecode(np.frombuffer(bg_data, np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 找到缺口边缘
            edge = cv2.Canny(gray, 100, 200)
            contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 分析缺口位置
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if 35 < w < 45 and 35 < h < 45:  # 缺口大小范围
                    return x
                    
            return None
            
        except Exception as e:
            self.logger.error(f"计算缺口位置失败: {str(e)}")
            return None

    def _do_slide(self, slider, track):
        """执行滑动"""
        try:
            # 点击并按住滑块
            ActionChains(self.driver).click_and_hold(slider).perform()
            
            # 根据轨迹移动
            for x in track:
                # 添加随机上下抖动
                y = random.randint(-2, 2)
                ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=y).perform()
                # 随机停顿
                time.sleep(random.uniform(0.01, 0.03))
            
            # 模拟人工抖动
            ActionChains(self.driver).move_by_offset(xoffset=-2, yoffset=0).perform()
            time.sleep(0.1)
            ActionChains(self.driver).move_by_offset(xoffset=2, yoffset=0).perform()
            
            # 松开滑块
            time.sleep(0.5)
            ActionChains(self.driver).release().perform()
            
            # 等待验证结果
            time.sleep(1.5)
            
            # 检查验证结果
            try:
                success = self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "tc-success"))
                )
                return True
            except:
                return False
                
        except Exception as e:
            self.logger.error(f"滑动操作失败: {str(e)}")
            return False

    def generate_slide_tracks(self, distance):
        """生成滑动轨迹"""
        tracks = []
        current = 0
        mid = distance * 3 / 4
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1/2 * a * t * t
            current += move
            tracks.append(round(move))
        
        return tracks

    def debug_captcha_response(self, response):
        """调试验证码响应"""
        try:
            self.logger.debug(f"验证码响应状态码: {response.status_code}")
            self.logger.debug(f"验证码响应头: {dict(response.headers)}")
            self.logger.debug(f"验证码响应内容: {response.text[:200]}...")  # 只显示前200个字符
            
            try:
                json_data = response.json()
                self.logger.debug(f"验证码JSON数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
            except:
                self.logger.debug("响应不是JSON格式")
                
        except Exception as e:
            self.logger.error(f"调试验证码响应时发生错误: {str(e)}")

    def _simulate_slide(self, distance):
        """模拟真实的滑动轨迹"""
        # 这个方法可以根据需要实现，用于生成更真实的滑动轨迹
        # 目前仅返回简的距离值
        return distance

    def submit_order(self, period_id, schedule_id, member_ticket_info_id, reserve_date=None):
        """提交订单"""
        try:
            # 如果没有指定预约日期，使用当前日期
            if reserve_date is None:
                reserve_date = datetime.now().strftime("%Y.%m.%d 00:00:00")

            # 1. 获取会员票务信息
            member_ticket_info = self.get_member_ticket_info()
            if not member_ticket_info:
                self.logger.error("获取会员票务信息失败")
                return None

            # 2. 检查验证码要求
            captcha_require = self.check_captcha_require()
            if not captcha_require:
                self.logger.error("检查验证码要求失败")
                return None

            # 3. 获取预约配置
            visitor_days = self.get_visitor_days(reserve_date)
            if not visitor_days:
                self.logger.error("获取预约配置失败")
                return None

            # 4. 获取服务器时间
            server_time = self.get_server_time()
            if not server_time:
                self.logger.error("获取服务器时间失败")
                return None

            # 5. 获取风险控制状态
            risk_open = self.get_risk_open()
            if not risk_open:
                self.logger.error("获取风险控制状态失败")
                return None

            # 6. 获取会员信息
            member_info = self.get_member_info()
            if not member_info:
                self.logger.error("获取会员信息败")
                return None

            # 7. 处理验证码
            if not self.handle_captcha():
                self.logger.error("验证码处理失败")
                return None

            # 8. 获取支付网关列表
            payment_gateway = self.get_payment_gateway_list()
            if not payment_gateway:
                self.logger.error("获取支网关列表失败")
                return None

            # 9. 获取风控token
            device_token = self.get_qq_security_token_with_retry()
            if not device_token:
                self.logger.error("获取风控token失败")
                return None

            # 10. 准备订单数据
            order_data = {
                "orderType": "ticket",
                "stadiumId": int(self.stadium_id),
                "platform": "APP",
                "details": [{
                    "scheduleId": int(schedule_id),
                    "quantity": 1,
                    "certificateReqs": [{
                        "memberTicketInfoId": int(member_ticket_info_id)
                    }]
                }],
                "fetchType": "1",
                "pay": {
                    "gatewayCode": "spdbBankPay:appWx",
                    "merchantCode": "spdbprod"
                },
                "appId": "wx1d7ddce169710ba7",
                "contactInfo": {
                    "certificateEncode": "44261FB36B9BDB49F009C560B02894B6FBD6C5ED58365B7F",
                    "certificateMd5": "5eafebb1e0d9f45263224b8158615205",
                    "certificateNo": "620105199902220015",
                    "certificateType": "idcard",
                    "realname": "潘秉宏",
                    "mobile": "19909442097"
                },
                "reservePeriodId": int(period_id)
            }

            # 11. 提交订单
            timestamp = str(int(time.time() * 1000))
            form_data = {
                "command": json.dumps(order_data, ensure_ascii=False),
                "orderReqTime": timestamp,
                "openId": "oY9oQ5D2tZLqEOoM7zundFGcMabk",
                "contactNumber": "5992ce0ec5c4da67f7f01e5e460b8bfe",
                "deviceToken": device_token,
                "openBuyTime": visitor_days['data']['openBuyTime'],
                "oStadiumId": self.stadium_id,
                "sstCode": "ssmtifri",
                "appId": "wx1d7ddce169710ba7"
            }

            url = f"{self.base_url}/vendor/member/order/payOrder.xhtml"
            response = self.session.post(url, headers=self.headers, data=form_data)
            
            return self._handle_order_response(response)
            
        except Exception as e:
            self.logger.error(f"提交订单失败: {str(e)}")
            return None

    def get_qq_security_token(self):
        """获取腾讯风控token"""
        # 先上报事件
        if not self.report_event():
            self.logger.error("事件上报失败")
            return None
        
        url = "https://flysec.m.qq.com/jprx/1941"
        
        qq_headers = {
            "Host": "flysec.m.qq.com",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN",
            "Accept": "*/*",
            "Origin": "https://servicewechat.com",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        try:
            content = self.generate_content()
            if not content:
                self.logger.error("生成content失败")
                return None

            data = {
                "req": {
                    "content": content,
                    "channel": "109027",
                    "token": self.qq_token,  # 使用初始化时设置的token
                    "version": "1",
                    "type": "1",
                    "timestamp": str(int(time.time() * 1000))
                }
            }
            
            self.logger.debug(f"风控请求数据: {json.dumps(data, ensure_ascii=False)}")
            response = self.session.post(url, headers=qq_headers, json=data, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"风控响应数据: {json.dumps(result, ensure_ascii=False)}")
                
                resp = result.get('data', {}).get('resp', {})
                if resp.get('ret') == 0:
                    # 更新token
                    if resp.get('token'):
                        self.qq_token = resp['token']
                    return resp.get('msgBlock')
                else:
                    self.logger.error(f"获取风控token失败，错误码: {resp.get('ret')}")
                    return None
            
            self.logger.error(f"风控请求失败，状态码: {response.status_code}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取风控token失败: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None

    def generate_content(self):
        """生成风控请求的content参数"""
        try:
            # 构建设备信息
            device_info = {
                "appName": "com.tencent.mm",
                "appVersion": "8.0.53",
                "deviceType": "iPhone",
                "osName": "iOS",
                "osVersion": "17.2.1",
                "vendorId": "A" * 40,  # 固定值
                "deviceId": "B" * 40,   # 固定值
                "deviceModel": "iPhone",
                "networkType": "WIFI",
                "operator": "",
                "pluginVersion": "1.0.0",
                "sdkVersion": "1.0.0",
                "timestamp": int(time.time() * 1000),
                "tokenId": self.qq_token
            }

            # 添加业务参数
            business_info = {
                "scene": "ticket",
                "sessionId": "a" * 32,  # 固定值
                "url": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html",
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN"
            }

            data = {
                "deviceInfo": device_info,
                "businessInfo": business_info,
                "timestamp": int(time.time() * 1000),
                "nonce": "a" * 32  # 固定值
            }
            
            # 转为JSON字符串并base64编码
            content = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
            return content
        except Exception as e:
            self.logger.error(f"生成content失败: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return None

    def update_token(self):
        """更新风控token"""
        try:
            # 这里需要实现token的更新逻辑
            # 可能需要调用其他接口或使用特定算法
            return "new_token_here"
        except Exception as e:
            self.logger.error(f"更新token失败: {str(e)}")
            return None

    def run(self):
        """运行抢票程序"""
        try:
            self.logger.info("\n" + "="*50)
            self.logger.info("欢迎使用自动抢票程序")
            self.logger.info("="*50 + "\n")

            # 获取用户选择
            selection = self.check_available_tickets()
            if not selection:
                self.logger.info("\n已退出预订程序")
                return

            self.logger.info("\n开始提交订单...")
            # 提交订单时传入预约日期
            result = self.submit_order(
                period_id=selection['period_id'],
                schedule_id=selection['schedule_id'],
                member_ticket_info_id=selection['member_ticket_info_id'],
                reserve_date=selection['date']  # 传入选择的日期
            )
            
            # 处理订单结果
            if result and result.get('success'):
                self.logger.info("\n" + "="*50)
                self.logger.info("订单提交成功！")
                self.logger.info(f"订单号: {result.get('data', {}).get('orderNo', '未知')}")
                self.logger.info("="*50)
            else:
                self.logger.error("\n" + "="*50)
                self.logger.error(f"订单提交失败: {result.get('msg') if result else '未知错误'}")
                self.logger.error("="*50)
            
        except Exception as e:
            self.logger.error(f"运行时发生错误: {str(e)}")

    def get_reserve_config(self):
        """获取预约配置"""
        try:
            # 1. 先获取问配置
            visitor_days = self.check_visitor_days()
            if not visitor_days or not visitor_days.get('success'):
                self.logger.error("获取访问配置失败")
                return None
            
            # 2. 获取服务器时间
            server_time = self.get_server_time()
            if not server_time or not server_time.get('success'):
                self.logger.error("获取服务器时间失败")
                return None
            
            # 3. 获取风控状态
            risk_open = self.get_risk_open()
            if not risk_open or not risk_open.get('success'):
                self.logger.error("获取风控状态失败")
                return None
            
            # 4. 取会员信息
            member_info = self.get_member_info()
            if not member_info or not member_info.get('success'):
                self.logger.error("获取会员信息失败")
                return None
            
            return {
                'visitor_days': visitor_days,
                'server_time': server_time,
                'risk_open': risk_open,
                'member_info': member_info
            }
        except Exception as e:
            self.logger.error(f"获取预约配置失败: {str(e)}")
            return None

    def get_visitor_days(self, reserve_date):
        """获取具体日期的预约配置"""
        url = f"{self.base_url}/vendor/reserve/getReserveVisitorDaysAndOpenMinutesByStadiumId.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "reserveDate": reserve_date,
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            self.logger.info(f"Visitor Days Response: {response.text}")
            return response.json()
        except Exception as e:
            self.logger.error(f"获取预约日期配置失败: {str(e)}")
            return None

    def get_risk_open(self):
        """获取风控状态"""
        url = f"{self.base_url}/vendor/member/getRiskOpen.xhtml"
        params = {
            "stadiumId": self.stadium_id,
            "orderType": "ticket2",
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            self.logger.info(f"Risk Open Response: {response.text}")
            return response.json()
        except Exception as e:
            self.logger.error(f"获取风控状态失败: {str(e)}")
            return None

    def get_member_info(self):
        """获取会员信息"""
        url = f"{self.base_url}/vendor/member/memberInfo.xhtml"
        params = {
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            self.logger.info(f"Member Info Response: {response.text}")
            return response.json()
        except Exception as e:
            self.logger.error(f"获取会员信息失败: {str(e)}")
            return None

    def check_available_tickets(self):
        """检查所有可用日期的余票情况并提供交互式选择"""
        self.logger.info("正在查询可用票务信息...\n")
        available_dates = self.get_available_dates()
        if not available_dates:
            self.logger.info("没有找到可用日期或获取数据失败")
            return None

        # 创建选项列表
        options = []
        self.logger.info("=== 可预订场次 ===")
        for date, info in available_dates.items():
            if info['total'] > 0:  # 只显示有票的场次
                self.logger.info(
                    f"日期: {date}\n"
                    f"  {'上午场' if info['morning']['tickets'] > 0 else '下午场'}: "
                    f"{info['morning']['tickets'] if info['morning']['tickets'] > 0 else info['afternoon']['tickets']}张"
                )
                # 添加有余票的场次选项中
                if info['morning']['tickets'] > 0:
                    options.append({
                        'date': date,
                        'period': 'morning',
                        'time': info['morning']['time'],
                        'period_id': info['morning']['period_id'],
                        'tickets': info['morning']['tickets']
                    })
                if info['afternoon']['tickets'] > 0:
                    options.append({
                        'date': date,
                        'period': 'afternoon',
                        'time': info['afternoon']['time'],
                        'period_id': info['afternoon']['period_id'],
                        'tickets': info['afternoon']['tickets']
                    })

        if not options:
            self.logger.info("\n当前没有可预订的场次")
            return None

        # 显示选项供用户选择
        self.logger.info("\n=== 请选择要预订的场次 ===")
        for i, opt in enumerate(options, 1):
            self.logger.info(f"{i}. {opt['date']} ({opt['time']}) - 剩余{opt['tickets']}张")
        self.logger.info("0. 退出")

        # 获取用户输入
        while True:
            try:
                choice = int(input("\n请输入选项编号: "))
                if choice == 0:
                    return None
                if 1 <= choice <= len(options):
                    selected = options[choice - 1]
                    self.logger.info(f"\n您选择了: {selected['date']} {selected['time']}")
                    return {
                        'date': selected['date'],
                        'period_id': selected['period_id'],
                        'schedule_id': self.schedule_id,
                        'member_ticket_info_id': "15982800"  # 这个ID可能需要动态获取
                    }
                else:
                    self.logger.info("无效的选项，请重新选择")
            except ValueError:
                self.logger.info("请输入有效的数字")

    def handle_captcha_with_retry(self, max_retries=3):
        """带重试制的验证码处理"""
        for i in range(max_retries):
            if self.handle_captcha():
                return True
            self.logger.info(f"验证失败，还有 {max_retries - i - 1} 次重试机会")
        return False

    def get_qq_security_token_with_retry(self, max_retries=3):
        """带试机制的获取风控token"""
        for i in range(max_retries):
            token = self.get_qq_security_token()
            if token:
                return token
            self.logger.info(f"获取风控token失败，还有 {max_retries - i - 1} 次重试机会")
            time.sleep(1)  # 等待1秒后重试
        return None

    def report_event(self):
        """上报事件到腾讯服务器"""
        url = "https://gatherer.m.qq.com/event/report"
        
        headers = {
            "Host": "gatherer.m.qq.com",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN",
            "Accept": "*/*",
            "Origin": "https://servicewechat.com",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        try:
            # 生成唯一请求ID
            import uuid
            req_id = str(uuid.uuid4())
            current_time = int(time.time() * 1000)
            
            data = {
                "channel": "109027",
                "platform": 6,
                "events": [
                    {
                        "id": "EId_UId_Init_Start",
                        "content": json.dumps({
                            "buildno": 28,
                            "reqId": req_id,
                            "t": current_time,
                            "ret": 0,
                            "msg": ""
                        })
                    },
                    {
                        "id": "EId_UId_Init_End",
                        "content": json.dumps({
                            "buildno": 28,
                            "reqId": req_id,
                            "t": current_time + 3,  # 模拟3ms的处理时间
                            "ret": 0,
                            "msg": "",
                            "dur": 3
                        })
                    }
                ]
            }
            
            response = self.session.post(url, headers=headers, json=data, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ret') == 0:
                    self.logger.debug("事件上报成功")
                    return True
                else:
                    self.logger.error(f"事件上报失败: {result}")
                    return False
            else:
                self.logger.error(f"事件上报请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"事件上报异常: {str(e)}")
            return False

    def get_member_ticket_info(self):
        """获取会员票务信息"""
        url = f"{self.base_url}/vendor/member/getMemberTicketInfoList.xhtml"
        params = {
            "appId": "wx1d7ddce169710ba7"
        }
        try:
            response = self.session.get(url, headers=self.headers, params=params)
            return response.json()
        except Exception as e:
            self.logger.error(f"获取会员票务信息失败: {str(e)}")
            return None

    def check_login_status(self):
        """检查登录状态"""
        try:
            # 通过获取会员信息来证登录状态
            url = f"{self.base_url}/vendor/member/memberInfo.xhtml"
            params = {
                "appId": "wx1d7ddce169710ba7"
            }
            response = self.session.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info("登录状态有效")
                    return True
                else:
                    self.logger.error(f"登录状态无效: {result.get('msg', '未知错误')}")
                    return False
            else:
                self.logger.error(f"检查登录状态失败: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            self.logger.error(f"查登录状态时发生错误: {str(e)}")
            return False

    def refresh_login(self):
        """刷新登录状态"""
        try:
            # 这里可以添加刷新登录的逻辑
            # 如果需要重新登录，可以在这里实现
            self.logger.info("尝试刷新登录状态...")
            
            # 示例：更新 headers 中的 mpsessid
            self.headers.update({
                "mpsessid": "1AC6E75AF592E04CEBB5C178E55F4ABB4E3F124010A7AA9036F30191B2E06E595D000213AF7F7230@f5786a6a"
            })
            
            # 验证新的登录状态
            if self.check_login_status():
                self.logger.info("登录状态刷新成功")
                return True
            else:
                self.logger.error("登录态刷新失败")
                return False
            
        except Exception as e:
            self.logger.error(f"刷新登录状态时发生错误: {str(e)}")
            return False

    def debug_captcha(self, bg_img, slider_img):
        """调试验证码识别"""
        try:
            # 保存图片用于调试
            with open('debug_bg.png', 'wb') as f:
                f.write(bg_img)
            with open('debug_slider.png', 'wb') as f:
                f.write(slider_img)
            
            # 计算并显示匹配结果
            distance = self.calculate_slide_distance(bg_img, slider_img)
            self.logger.debug(f"调试模式 - 计算得到的滑动距离: {distance}px")
            return distance
        except Exception as e:
            self.logger.error(f"调试验证码识别失败: {str(e)}")
            return None

    def _handle_order_response(self, response):
        """处理订单提交响应"""
        try:
            if response.status_code != 200:
                self.logger.error(f"订单提交失败: HTTP {response.status_code}")
                return None
            
            result = response.json()
            if result.get('success'):
                self.logger.info("订单提交成功")
                return result
            else:
                self.logger.error(f"订单提交失败: {result.get('msg', '未知错误')}")
                return result
            
        except Exception as e:
            self.logger.error(f"处理订单响应时发生错误: {str(e)}")
            return None

    def _retry_operation(self, operation, max_retries=3, delay=1):
        """通用重试机制"""
        for i in range(max_retries):
            try:
                result = operation()
                if result:
                    return result
            except Exception as e:
                self.logger.error(f"操作失败 ({i+1}/{max_retries}): {str(e)}")
            
            if i < max_retries - 1:
                self.logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        return None

    def get_captcha_esid(self):
        """获取验证码 ESId"""
        try:
            # 等待验证码加载
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "tcaptcha_iframe"))  # 根据实际情况调整iframe定位
            )
            # 切换到验证码iframe
            self.driver.switch_to.frame(iframe)
            
            # 获取ESId (通常在URL或页面元素中)
            esid = None
            try:
                # 方法1: 从URL获取
                current_url = self.driver.current_url
                # 解析URL中的ESId参数
                if 'ESId=' in current_url:
                    esid = current_url.split('ESId=')[1].split('&')[0]
            except:
                pass
            
            if not esid:
                try:
                    # 方法2: 从页面元素获取
                    esid_element = self.wait.until(
                        EC.presence_of_element_located((By.ID, "esid"))  # 根据实际情况调整元素定位
                    )
                    esid = esid_element.get_attribute('value')
                except:
                    pass
            
            if not esid:
                self.logger.error("未找到ESId")
                return None
            
            return esid
            
        except Exception as e:
            self.logger.error(f"获取ESId失败: {str(e)}")
            return None
        finally:
            # 切回主框架
            self.driver.switch_to.default_content()

    def get_and_verify_captcha(self):
        """处理滑块验证码"""
        try:
            # 首先获取ESId
            esid = self.get_captcha_esid()
            if not esid:
                return False
            
            # 切换到验证码iframe
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "tcaptcha_iframe"))
            )
            self.driver.switch_to.frame(iframe)
            
            # 等待滑块元素加载
            slider = self.wait.until(
                EC.presence_of_element_located((By.ID, "tcaptcha_drag_thumb"))  # 根据实际情况调整定位
            )
            
            # 获取验证码背景图
            bg_img = self.wait.until(
                EC.presence_of_element_located((By.ID, "slideBg"))  # 根据实际情况调整定位
            )
            
            # 计算滑动距离
            distance = self._calculate_distance(bg_img)
            if not distance:
                return False
            
            # 生成滑动轨迹
            track = self._generate_track(distance)
            
            # 执行滑动
            success = self._simulate_drag(slider, track)
            
            return success
            
        except Exception as e:
            self.logger.error(f"滑块验证失败: {str(e)}")
            return False
        finally:
            # 切回主框架
            try:
                self.driver.switch_to.default_content()
            except:
                pass

    def _calculate_distance(self, bg_img):
        """计算滑块缺口距离"""
        try:
            # 下载并保存背景图
            bg_url = bg_img.get_attribute('src')
            bg_data = self._download_image(bg_url)
            
            # 使用 OpenCV 识别缺口位置
            img = cv2.imdecode(np.frombuffer(bg_data, np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edge = cv2.Canny(gray, 100, 200)
            
            # 找到缺口轮廓
            contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if 40 < w < 60 and 40 < h < 60:  # 缺口大小范围
                    return x
            
            return None
            
        except Exception as e:
            self.logger.error(f"计算滑动距离失败: {str(e)}")
            return None

    def _generate_track(self, distance):
        """生成人工滑动轨迹"""
        track = []
        current = 0
        mid = distance * 3/4
        t = 0.2
        v = 0
        
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1/2 * a * t * t
            current += move
            track.append(round(move))
        
        # 微调
        while sum(track) > distance:
            track[-1] -= 1
        while sum(track) < distance:
            track[-1] += 1
            
        return track

    def _simulate_drag(self, slider, track):
        """模拟人工滑动"""
        try:
            ActionChains(self.driver).click_and_hold(slider).perform()
            
            # 按轨迹移动
            for x in track:
                ActionChains(self.driver).move_by_offset(
                    xoffset=x,
                    yoffset=random.randint(-2, 2)  # 添加随机上下抖动
                ).perform()
                time.sleep(random.uniform(0.01, 0.03))  # 随机停顿
            
            # 模拟抖动
            ActionChains(self.driver).move_by_offset(xoffset=-2, yoffset=0).perform()
            ActionChains(self.driver).move_by_offset(xoffset=2, yoffset=0).perform()
            
            time.sleep(0.5)  # 停顿一下
            ActionChains(self.driver).release().perform()
            
            # 检查验证结果
            time.sleep(1)
            success = self._check_success()
            return success
            
        except Exception as e:
            self.logger.error(f"模拟滑动失败: {str(e)}")
            return False

    def _check_success(self):
        """检查验证是否成功"""
        try:
            # 这里需要根据实际情况调整成功的判断条件
            success_element = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "verify-success"))
            )
            return True if success_element else False
        except:
            return False

    def _download_image(self, url):
        """下载图片"""
        response = self.session.get(url)
        return response.content

if __name__ == "__main__":
    bot = TicketBot()
    bot.run()