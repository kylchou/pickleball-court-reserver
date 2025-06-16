"""WebDriver setup."""
from __future__ import annotations

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

log = logging.getLogger(__name__)


def make_driver(headless: bool = True) -> webdriver.Chrome:
    """Build a Chrome WebDriver, headless by default so this can run on a cron/task scheduler."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # Avoid getting flagged as an obvious bot by sites that check this.
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    log.info("Chrome WebDriver started (headless=%s)", headless)
    return driver
