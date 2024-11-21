class Config:
    # 调试模式
    DEBUG = True
    
    # 基础配置
    BASE_URL = "https://rce.tencentrio.com/sstmticket/sam"
    STADIUM_ID = "69001"
    SCHEDULE_ID = "61038"
    CAPTCHA_APP_ID = "2013697930"
    
    # 请求头
    HEADERS = {
        "Host": "rce.tencentrio.com",
        "Connection": "keep-alive",
        "content-type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip,compress,br,deflate",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x18003530) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wx1d7ddce169710ba7/83/page-frame.html"
    }
