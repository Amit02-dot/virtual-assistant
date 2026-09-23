import time
import os
from playwright.sync_api import sync_playwright

class BrowserAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
            # Use persistent context to keep login sessions
            user_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "JarvisBrowser")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir,
                headless=False, # Show browser so user can see it
                args=["--start-maximized"],
                no_viewport=True
            )
            
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
    def stop(self):
        if self.context:
            self.context.close()
            self.context = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def navigate(self, url):
        self.start()
        try:
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            return True
        except Exception as e:
            print(f"Browser navigate error: {e}")
            return False

    def get_page_summary(self):
        """Returns simplified text of the page to feed to the LLM"""
        if not self.page:
            return ""
        try:
            # Extract basic text
            text = self.page.evaluate("document.body.innerText")
            return text[:10000] # Limit size for LLM
        except:
            return ""

    def take_screenshot(self, filename="browser_temp.png"):
        if not self.page:
            return None
        try:
            self.page.screenshot(path=filename)
            return filename
        except:
            return None

    def click(self, selector):
        if not self.page: return False
        try:
            self.page.click(selector, timeout=5000)
            time.sleep(1)
            return True
        except:
            return False

    def type_text(self, selector, text):
        if not self.page: return False
        try:
            self.page.fill(selector, text, timeout=5000)
            return True
        except:
            return False

    def get_url(self):
        if not self.page: return ""
        return self.page.url
