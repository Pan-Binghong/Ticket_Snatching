from datetime import datetime
import time

class OrderService:
    def __init__(self, session, logger, config, risk_service):
        self.session = session
        self.logger = logger
        self.config = config
        self.risk_service = risk_service
        self.base_url = config.BASE_URL
        
    def get_available_dates(self):
        """获取可预订日期"""
        self.logger.info("正在获取可预订日期...")
        try:
            url = f"{self.base_url}/vendor/reserve/getReserveVisitorDaysAndOpenMinutesByStadiumId.xhtml"
            params = {
                "stadiumId": self.config.STADIUM_ID,
                "reserveDate": datetime.now().strftime("%Y-%m-%d"),
                "appId": self.config.APP_ID
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return self._parse_available_dates(result.get("data", {}))
                self.logger.error(f"获取可预订日期失败: {response.text}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取可预订日期时发生错误: {str(e)}")
            return None
        
    def _parse_available_dates(self, data):
        """解析可用日期数据"""
        available_dates = {}
        try:
            for date_info in data.get("visitorDays", []):
                date = date_info.get("visitorDay")
                if not date:
                    continue
                
                sessions = {}
                # 上午场
                if date_info.get("morningTicketNumber", 0) > 0:
                    sessions["morning"] = {
                        "time": "09:30-12:30",
                        "tickets": date_info["morningTicketNumber"]
                    }
                    self.logger.info(f"\n日期: {date}")
                    self.logger.info(f"  上午场 (09:30-12:30): {date_info['morningTicketNumber']}张")
                
                # 下午场
                if date_info.get("afternoonTicketNumber", 0) > 0:
                    sessions["afternoon"] = {
                        "time": "12:30-15:00",
                        "tickets": date_info["afternoonTicketNumber"]
                    }
                    if not sessions.get("morning"):
                        self.logger.info(f"\n日期: {date}")
                    self.logger.info(f"  下午场 (12:30-15:00): {date_info['afternoonTicketNumber']}张")
                
                if sessions:
                    available_dates[date] = sessions
            
            return available_dates
            
        except Exception as e:
            self.logger.error(f"解析日期数据时发生错误: {str(e)}")
            return None
        
    def check_available_tickets(self):
        """检查可用票务"""
        self.logger.info("正在查询可用票务信息...\n")
        available_dates = self.get_available_dates()
        
        if not available_dates:
            self.logger.info("没有找到可用日期或获取数据失败")
            return None
            
        # 显示可预订场次
        self.logger.info("=== 可预订场次 ===")
        options = []
        option_index = 1
        
        for date, sessions in available_dates.items():
            self.logger.info(f"日期: {date}")
            for session_type, info in sessions.items():
                if session_type == "morning":
                    self.logger.info(f"  上午场: {info['tickets']}张")
                else:
                    self.logger.info(f"  下午场: {info['tickets']}张")
                
                options.append({
                    "date": date,
                    "session": session_type,
                    "time": info["time"],
                    "tickets": info["tickets"]
                })
                
        # 显示选择菜单
        self.logger.info("\n=== 请选择要预订的场次 ===")
        for i, option in enumerate(options, 1):
            self.logger.info(f"{i}. {option['date']} ({option['time']}) - 剩余{option['tickets']}张")
        self.logger.info("0. 退出")
        
        # 获取用户选择
        try:
            choice = input("\n请输入场次编号: ").strip()
            if choice == "0":
                return None
            
            choice = int(choice)
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                self.logger.info(f"\n您选择了: {selected['date']} {selected['time']}")
                return selected
                
        except ValueError:
            self.logger.error("输入无效")
            
        return None
        
    def submit_order(self, selection):
        """提交订单"""
        if not selection:
            return None
            
        self.logger.info("\n开始提交订单...")
        try:
            # 获取预约日期信息
            visitor_days = self._get_visitor_days()
            self.logger.info(f"Visitor Days Response: {visitor_days}")
            
            # 获取风控token
            token = self.risk_service.get_security_token()
            if not token:
                self.logger.error("获取风控token失败")
                return None
                
            # 构建订单数据
            order_data = self._build_order_data(selection, token)
            
            # 提交订单
            response = self._submit_order_request(order_data)
            return self._handle_order_response(response)
            
        except Exception as e:
            self.logger.error(f"提交订单失败: {str(e)}")
            return None
