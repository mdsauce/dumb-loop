from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import urllib, urllib.error
import threading
import socket
import queue
from selenium.common.exceptions import WebDriverException
from sauceclient import SauceClient
import random
import logging
import datetime
import time
import os, sys
THREADLIMIT = 50
TESTS = 1500
username = os.environ.get('SAUCE_USERNAME')
access_key = os.environ.get('SAUCE_ACCESS_KEY')
sauce_client = SauceClient(username, access_key)
now = datetime.datetime.now()
logfileName = now.strftime('job-runner_%d-%m-%Y_%H-%M.log')
logging.basicConfig(filename=logfileName,level=logging.INFO)

def capsBuilder():
    testName = "Simple Mac Test"
    platforms = ["macOS 10.13", "macOS 10.12", "macOS 10.11", "macOS 10.10", "macOS 10.9"]
    browsers = ["chrome", "firefox", "safari"]
    caps = {
        'platform': random.choice(platforms),
        'browserName': random.choice(browsers),
        'version': "latest",
        'seleniumVersion': "3.8.1",
        'name': testName
    }
    return caps

def randomTest(caps):
    try:
        driver = webdriver.Remote(command_executor="http://{}:{}@ondemand.saucelabs.com/wd/hub".format(username, access_key), desired_capabilities=caps)
    except urllib.error.URLError as u:
        logging.exception("Problem creating remote webdriver session. Potential DNS rate limiting.\n{}".format(u))
        return 1
    except socket.gaierror as s:
        logging.info("Problem creating remote webdriver session at the socket level. Potential DNS rate limiting.\n{}".format(u))
        return 1
    try:
        driver.get("https://saucelabs.com")
        wait = WebDriverWait(driver, 45)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "site-container")))
        if driver.title == "Cross Browser Testing, Selenium Testing, and Mobile Testing | Sauce Labs":
            sauce_client.jobs.update_job(driver.session_id, passed=True)
            logging.info(f"Session {driver.session_id} passed")
            driver.quit()
            return 0
        else:
            sauce_client.jobs.update_job(driver.session_id, passed=False)
            logging.info("Session {} failed".format(driver.session_id))
            session = driver.session_id
            driver.quit()
            return session
    except WebDriverException as m:
        logging.exception(f"Session {driver.session_id} failed due to a Web Driver Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{m}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        return driver.session_id
    except (socket.timeout, socket.gaierror, urllib.error.URLError, urllib.error.HTTPError) as s:
        logging.exception(f"Session {driver.session_id} failed due to a Socket or URL Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{s}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        driver.quit()
        return session
    except TimeoutError as t:
        logging.exception(f"Session {driver.session_id} failed due to a Timeout Exception! https://saucelabs.com/beta/tests/{driver.session_id}\n{t}")
        sauce_client.jobs.update_job(driver.session_id, passed=False)
        session = driver.session_id
        driver.quit()
        return session

lock = threading.Lock()

def worker(q):
    global jobNumber
    global failedJobs
    while True:
        if q.empty():
            logging.info(f"Thread-{threading.current_thread().name} can't find any more work because the queue is empty.")
        # To get around the upstream DNS rate limit.
        # 12 seconds is OK for ~ 1500 jobs.  Only 1 error
        time.sleep(random.randrange(5,14))
        test = q.get()
        status = randomTest(test)
        with lock:
            if status != 0:
                failedJobs+=1
                print(f"Thread-{threading.current_thread().name} says: I might be blocking the .join()")
                logging.info(f"Thread-{threading.current_thread().name} has a failed job.")
                if status != 1:
                    logging.info(f"Thread-{threading.current_thread().name} had failed session: {status}.")
        with lock:
            jobNumber+=1
            logging.info(f"Thread-{threading.current_thread().name} finished job number: {jobNumber}")
            print(f"Job {jobNumber} finished")
            q.task_done()

capsToTest = queue.Queue()
for i in range(TESTS):
    capsToTest.put(capsBuilder())

jobNumber = 0
failedJobs = 0

print(f"Logged to {logfileName}")

for i in range(THREADLIMIT):
    w = threading.Thread(name=i, target=worker, args=(capsToTest,))
    w.setDaemon(True)
    w.start()

capsToTest.join()
logging.info(f"Total Jobs Run: {TESTS}\nFailed Job Count: {failedJobs}")
print(f"Failed Jobs: {failedJobs}")
