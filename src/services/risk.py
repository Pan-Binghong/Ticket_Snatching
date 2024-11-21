import json
import time
import base64
import uuid

class RiskService:
    def __init__(self, session, logger, config):
        self.session = session
        self.logger = logger
        self.config = config
        self.base_url = "https://flysec.m.qq.com"

    def get_security_token_with_retry(self, max_retries=3):
        """获取风控token（带重试）"""
        for i in range(max_retries):
            try:
                token = self._get_security_token()
                if token:
                    return token
                self.logger.info(f"获取风控token失败，还有 {max_retries - i - 1} 次重试机会")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"获取风控token异常: {str(e)}")
        return None

    def _get_security_token(self):
        """获取风控token的具体实现"""
        try:
            # 先上报事件
            if not self.report_event():
                return None

            # 获取token
            url = f"{self.base_url}/security/token"
            headers = {
                "Host": "flysec.m.qq.com",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
                "User-Agent": self.config.HEADERS["User-Agent"]
            }
            
            data = {
                "appId": self.config.CAPTCHA_APP_ID,
                "scene": "order"
            }
            
            response = self.session.post(url, json=data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return result.get("token")
                    
            self.logger.error(f"获取风控token失败: {response.text}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取风控token异常: {str(e)}")
            return None

    def report_event(self):
        """上报事件"""
        url = f"{self.base_url}/report/1941"
        headers = {
            "Host": "flysec.m.qq.com",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": self.config.HEADERS["User-Agent"],
            "Accept": "*/*",
            "Origin": "https://servicewechat.com",
            "Referer": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        
        try:
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
                            "t": current_time + 3,
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

    def _generate_content(self):
        """生成风控请求的content参数"""
        try:
            device_info = {
                "appName": "com.tencent.mm",
                "appVersion": "8.0.53",
                "deviceType": "iPhone",
                "osName": "iOS",
                "osVersion": "17.2.1",
                "vendorId": "A" * 40,
                "deviceId": "B" * 40,
                "deviceModel": "iPhone",
                "networkType": "WIFI",
                "operator": "",
                "pluginVersion": "1.0.0",
                "sdkVersion": "1.0.0",
                "timestamp": int(time.time() * 1000),
                "tokenId": self.qq_token
            }

            business_info = {
                "scene": "ticket",
                "sessionId": "a" * 32,
                "url": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html",
                "userAgent": self.config.HEADERS["User-Agent"]
            }

            data = {
                "deviceInfo": device_info,
                "businessInfo": business_info,
                "timestamp": int(time.time() * 1000),
                "nonce": "a" * 32
            }
            
            return base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
        except Exception as e:
            self.logger.error(f"生成content失败: {str(e)}")
            return None
