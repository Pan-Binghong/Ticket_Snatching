from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import cv2
import numpy as np
import time
import random
import requests

class CaptchaService:
    def __init__(self, driver, wait, logger, session=None):
        self.driver = driver
        self.wait = wait
        self.logger = logger
        self.session = session or requests.Session()
    
    def handle_captcha_with_retry(self, max_retries=3):
        """带重试机制的验证码处理"""
        for i in range(max_retries):
            if self.handle_slider_captcha():
                return True
            self.logger.info(f"验证失败，还有 {max_retries - i - 1} 次重试机会")
        return False
    
    def handle_slider_captcha(self):
        """处理滑块验证码"""
        try:
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "tcaptcha_iframe"))
            )
            self.driver.switch_to.frame(iframe)
            
            slider = self.wait.until(
                EC.presence_of_element_located((By.ID, "tcaptcha_drag_thumb"))
            )
            
            bg_img = self.wait.until(
                EC.presence_of_element_located((By.ID, "slideBg"))
            )
            
            distance = self._calculate_distance(bg_img)
            if not distance:
                return False
                
            track = self._generate_track(distance)
            success = self._simulate_drag(slider, track)
            
            return success
            
        except Exception as e:
            self.logger.error(f"滑块验证失败: {str(e)}")
            return False
        finally:
            try:
                self.driver.switch_to.default_content()
            except:
                pass
    
    def _calculate_distance(self, bg_img):
        """计算滑块缺口距离"""
        try:
            bg_url = bg_img.get_attribute('src')
            bg_data = self._download_image(bg_url)
            
            img = cv2.imdecode(np.frombuffer(bg_data, np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edge = cv2.Canny(gray, 100, 200)
            
            contours, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if 40 < w < 60 and 40 < h < 60:
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
        
        while sum(track) > distance:
            track[-1] -= 1
        while sum(track) < distance:
            track[-1] += 1
            
        return track
    
    def _simulate_drag(self, slider, track):
        """模拟人工滑动"""
        try:
            ActionChains(self.driver).click_and_hold(slider).perform()
            
            for x in track:
                ActionChains(self.driver).move_by_offset(
                    xoffset=x,
                    yoffset=random.randint(-2, 2)
                ).perform()
                time.sleep(random.uniform(0.01, 0.03))
            
            ActionChains(self.driver).move_by_offset(xoffset=-2, yoffset=0).perform()
            ActionChains(self.driver).move_by_offset(xoffset=2, yoffset=0).perform()
            
            time.sleep(0.5)
            ActionChains(self.driver).release().perform()
            
            time.sleep(1)
            return self._check_success()
            
        except Exception as e:
            self.logger.error(f"模拟滑动失败: {str(e)}")
            return False
    
    def _check_success(self):
        """检查验证是否成功"""
        try:
            success_element = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "verify-success"))
            )
            return True if success_element else False
        except:
            return False
    
    def _download_image(self, url):
        """下载图片"""
        try:
            response = self.session.get(url, verify=False)
            return response.content
        except Exception as e:
            self.logger.error(f"下载图片失败: {str(e)}")
            return None
