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
    # 全て満席でも通知を送信するか(T:常に送信, F:空きがあるときだけ送信)
    ntfy_always = event["ntfy_always"]
    
    # レストラン空き状況ページ
    url = f"https://reserve.tokyodisneyresort.jp/restaurant/calendar/?searchUseDate={date}&searchAdultNum=2&searchChildNum=0&searchChildAgeInform=&searchWheelchairCount=0&searchStretcherCount=0&searchNameCd=RLGC0&searchKeyword=&reservationStatus=0&searchRestaurantTypeList=7&nameCd=RLGC0&contentsCd=03&useDate={date}&mealDivList=3&adultNum=2&childNum=0&childAgeInform=&wheelchairCount=0&stretcherCount=0"
    
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
    
    # 時間帯・空き状況をそれぞれリストにまとめる
    list_time = list()
    list_status = list()
    for i in range(len(status_all)):
        if ':' in status_all[i]:
            list_time.append(status_all[i])
            if i<=len(status_all) and status_all[i+1]=='満席':
                list_status.append('満席')
            else:
                list_status.append('空席')
    
    # 文字列にまとめる    
    status_str = f"\n{date}の空き状況"
    # 満席以外の時間帯の数
    num_not_full = 0

    for i in range(len(list_status)):
        status_str += "\n" + list_time[i] + " : " + list_status[i]
        
        # 満席でない時間帯があれば、num_not_fullに1を足す
        if list_status[i] != "満席":
            num_not_full += 1
    
    # 空きがあれば文字列追加
    if num_not_full > 0:
        status_str = "\n空いている時間帯があります!!" + status_str + "\nURL : " + url
    
    # LINEに通知を送信
    if (ntfy_always=='T') or (ntfy_always=='F' and num_not_full>0):
        for t in token:
            # 各tokenに対して通知を送信
            line_ntfy(status_str, token=t)

    # webdriverを閉じる
    driver.quit()

    # 前回までのコンテキストが再利用されることがあるらしいく、'No space left on device'になるのを防ぐためtmpファイルを削除
    remove_unnecessary_file()

    return status_str


# %%
