import logging
import os
from datetime import datetime

def setup_logger(name):
    # 确保日志目录存在
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # 创建文件处理器
    file_handler = logging.FileHandler(
        f'log/ticket_bot.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
