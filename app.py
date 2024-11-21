from src.bot import TicketBot
from src.utils.logger import setup_logger

def main():
    logger = setup_logger('main')
    bot = None
    
    try:
        logger.info("正在启动自动抢票程序...")
        bot = TicketBot()
        
        if not bot.stadium_id:
            logger.info("未选择场馆，程序退出")
            return
            
        bot.run()
        
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        
    finally:
        try:
            if bot and hasattr(bot, 'cleanup'):
                bot.cleanup()
        except Exception as e:
            logger.error(f"清理资源时发生错误: {str(e)}")

if __name__ == "__main__":
    main()