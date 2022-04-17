# %%
import time
import os
import shutil
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# %%
def move_bin(fname, src_dir = "/opt", dest_dir = "/tmp/bin"):
    """/opt配下のファイルを/tmp/bin配下へ移動"""

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    dest_file = os.path.join(dest_dir, fname)
    shutil.copy2(os.path.join(src_dir, fname), dest_file)
    os.chmod(dest_file, 0o775)

def remove_unnecessary_file():
    """/tmp/binディレクトリを消去"""
    if os.path.exists('/tmp/bin/'):
        shutil.rmtree('/tmp/bin/')

def line_ntfy(mess, token):
    """LINE通知を送信する関数"""
    
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": "Bearer " + token}
    payload = {"message": str(mess)}
    requests.post(url, headers=headers, params=payload)

# %%
def lambda_handler(event, context):

    # /tmp/bin配下に移動
    move_bin("headless-chromium")
    move_bin("chromedriver")

    # 対象日付(yyyymmdd)
    date = event["date"]
    # LINE notifyのトークン
    token = event["token"]
    
    # レストラン空き状況ページ
    url = f"https://reserve.tokyodisneyresort.jp/restaurant/calendar/?searchUseDate={date}&searchAdultNum=2&searchChildNum=0&searchChildAgeInform=&searchWheelchairCount=0&searchStretcherCount=0&searchNameCd=RLGC0&searchKeyword=&reservationStatus=0&searchRestaurantTypeList=7&nameCd=RLGC0&contentsCd=03&useDate=20220428&mealDivList=3&adultNum=2&childNum=0&childAgeInform=&wheelchairCount=0&stretcherCount=0"
    
    # ユーザーエージェントがないと弾かれるので設定
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
    
    options = Options()
    options.binary_location = "/tmp/bin/headless-chromium"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={user_agent}")
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-tools')
    options.add_argument('--no-zygote')
    options.add_argument('--single-process')
    options.add_argument('--lang=ja-JP')
    options.add_argument('window-size=1920,1080')
    
    driver = webdriver.Chrome(
        executable_path='/tmp/bin/chromedriver',
        options=options
        )
    driver.get(url)
    driver.implicitly_wait(120)
    
    # 表が2つに分かれているのでそれぞれを取得
    # 1つめ
    status_1 = driver.find_element(By.XPATH, '//*[@id="restaurant_0"]/div[2]/div[2]/div/div/ul[1]').text
    # 2つめ
    driver.find_element(By.CLASS_NAME, 'next').click()
    status_2 = driver.find_element(By.XPATH, '//*[@id="restaurant_0"]/div[2]/div[2]/div/div/ul[1]').text
    status_all = (status_1 + '\n' + status_2).split('\n')
    
    # 文字列にまとめる    
    status_str = f"{date}の空き状況"
    # 満席以外の時間帯の数
    num_not_full = 0

    for i in range(round(len(status_all) / 2)):
        # status_allの偶数番目には時間帯が、奇数番目には空き状況が格納されている
        status_str += "\n" + status_all[2 * i] + " : " + status_all[2 * i + 1]
        
        # 満席でない時間帯があれば、num_not_fullに1足す
        if status_all[2 * i + 1] != "満席":
            num_not_full += 1
    
    # 空きがあれば文字列追加
    if num_not_full > 0:
        status_str = "空いている時間帯があります!!\n" + status_str
    
    # LINEに通知を送信
    line_ntfy(status_str, token)

    # webdriverを閉じる
    driver.quit()

    # 前回までのコンテキストが再利用されることがあるらしいく、'No space left on device'になるのを防ぐためtmpファイルを削除
    remove_unnecessary_file()

    return status_str

