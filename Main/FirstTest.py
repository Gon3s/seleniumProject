import sys

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument("user-data-dir=C:\\Users\\gones\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1") #Path to your chrome profile
driver = webdriver.Chrome(executable_path=r'C:/Users/gones/PycharmProjects/seleniumProject/Drivers/chromedriver.exe', options=options)

driver.get("https://www.ea.com/fr-fr/fifa/ultimate-team/web-app/")
driver.maximize_window()
delay = 20 # seconds

if False:
    try:
        loginButton = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Login"]/div/div/button[1][not(@disabled)]')))
        loginButton.click()
    except TimeoutException:
        print("Loading took too much time!")
        driver.close()
        sys.exit()
    #
    driver.find_element_by_id('email').send_keys('gones43@gmail.com')
    driver.find_element_by_id('password').send_keys('30juin2010OR')
    driver.find_element_by_id('btnLogin').click()
else:
    try:
        transfertList = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, '/html/body/main/section/section/div[2]/div/div/div[9]')))
        transfertList.click()
    except TimeoutException:
        print("Loading took too much time!")
        driver.close()
        sys.exit()



print(driver.title)
print(driver.current_url)

