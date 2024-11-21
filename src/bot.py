from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import requests
import urllib3
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .services.captcha import CaptchaService
from .services.risk import RiskService
from .services.auth import AuthService
from .services.order import OrderService
from .utils.logger import setup_logger
from .config import Config

class TicketBot:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.logger.info("初始化 TicketBot...")
        self.session = self._setup_session()
        
        # 配置 Chrome 选项
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        # chrome_options.add_argument('--headless')  # 无头模式，如果需要的话
        
        try:
            # 使用 webdriver_manager 自动管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
        except Exception as e:
            self.logger.error(f"Chrome 浏览器初始化失败: {str(e)}")
            raise Exception(f"浏览器初始化失败: {str(e)}")
        
        self.wait = WebDriverWait(self.driver, 10)
        
        self.captcha_service = CaptchaService(
            self.driver, 
            self.wait, 
            self.logger,
            session=self.session
        )
        self.risk_service = RiskService(self.session, self.logger, Config)
        self.auth_service = AuthService(self.session, self.logger, Config)
        self.order_service = OrderService(
            self.session, 
            self.logger, 
            Config, 
            risk_service=self.risk_service
        )
        
        # 场馆信息字典
        self.stadiums = {
            "1": {"id": "69001", "name": "上海天文馆"},
            "2": {"id": "69002", "name": "上海自然博物馆"}
        }
        
        # 选择场馆
        self.stadium_id = self.select_stadium()
        if not self.stadium_id:
            raise Exception("未选择场馆")
        
        self._initialize()
    
    def _setup_session(self):
        session = requests.Session()
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.headers.update(Config.HEADERS)
        return session
    
    def _initialize(self):
        """初始化检查"""
        self.logger.info("检查登录状态...")
        if not self.auth_service.check_login_status():
            self.logger.warning("登录状态无效，尝试刷新登录...")
            if not self.auth_service.refresh_login():
                raise Exception("登录状态无效")
        
        self.logger.info("预热风控token...")
        token = self.risk_service.get_security_token_with_retry()
        if not token:
            self.logger.warning("预热风控token失败，继续执行...")
    
    def run(self):
        """运行抢票程序"""
        try:
            self.logger.info("\n==================================================")
            self.logger.info("欢迎使用自动抢票程序")
            self.logger.info("==================================================\n")
            
            # 检查登录状态
            if not self.auth_service.check_login():
                self.logger.error("登录状态无效")
                return
            
            # 预热风控token
            self.logger.info("预热风控token...")
            self.risk_service.get_security_token_with_retry()
            
            # 查询可用票务
            selection = self.order_service.check_available_tickets()
            if not selection:
                self.logger.info("\n已退出预订程序")
                return
            
            # 提交订单
            order_result = self.order_service.submit_order(selection)
            if order_result:
                self.logger.info("订单提交成功！")
            else:
                self.logger.error("订单提交失败")
            
        except Exception as e:
            self.logger.error(f"运行时发生错误: {str(e)}")
        finally:
            self.cleanup()
    
    def select_stadium(self):
        """选择要预订的场馆"""
        self.logger.info("\n=== 请选择要预订的场馆 ===")
        for key, stadium in self.stadiums.items():
            self.logger.info(f"{key}. {stadium['name']}")
        self.logger.info("0. 退出")
        
        while True:
            try:
                choice = input("\n请输入场馆编号: ")
                if choice == "0":
                    return None
                if choice in self.stadiums:
                    selected = self.stadiums[choice]
                    self.logger.info(f"\n您选择了: {selected['name']}")
                    return selected["id"]
                else:
                    self.logger.info("无效的选项，请重新选择")
            except ValueError:
                self.logger.info("请输入有数字")
    
    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'driver'):
                self.logger.info("正在关闭浏览器...")
                self.driver.quit()
        except Exception as e:
            self.logger.error(f"清理资源时发生错误: {str(e)}")
