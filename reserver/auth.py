"""Login flow for the booking portal."""
from __future__ import annotations

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

log = logging.getLogger(__name__)


def login(driver, portal_url: str, username: str, password: str, timeout: int = 15) -> None:
    driver.get(portal_url)

    wait = WebDriverWait(driver, timeout)
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password_field = driver.find_element(By.NAME, "password")

    username_field.clear()
    username_field.send_keys(username)
    password_field.clear()
    password_field.send_keys(password)

    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit.click()

    # Confirm we actually landed on a logged-in page instead of an error banner.
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='account-menu']")))
    log.info("Logged in as %s", username)
