from selenium import webdriver
import time
import json
import requests
import re
import random
import traceback
from os import listdir
from os.path import isfile, join
from datetime import datetime

# user_name
user = 'jesse9025@gmail.com'
# passwd
passwd = 'Pw_wxgzh_xqwz_1332'
# Crawling list
gzlist = ['ifanr']

# login-in, get cookies, and save to local
def wechat_login():
    post = {} # cookies

    print('---- 启动浏览器， 打开微信公众号登录界面')
    driver = webdriver.Chrome()
    try:
        driver.get('https://mp.weixin.qq.com/')
        time.sleep(5) # sleep for 5 seconds
        print('---- Typing in Usr/Pw')
        driver.find_element_by_xpath("./*//input[@name='account']").clear() # clear user input
        driver.find_element_by_xpath("./*//input[@name='account']").send_keys(user) # type in usr
        driver.find_element_by_xpath("./*//input[@name='password']").clear() # clear password
        driver.find_element_by_xpath("./*//input[@name='password']").send_keys(passwd) # type in usr

        # print('---- 请点击：记住账号')
        driver.find_element_by_xpath("./*//i[@class='icon_checkbox']").click()
        time.sleep(1)
        driver.find_element_by_xpath("./*//a[@class='btn_login']").click()
        print('---- 扫描二维码登录')
        # https://mp.weixin.qq.com/cgi-bin/bizlogin?
        # action=validate
        # &lang=zh_CN
        # &account=jesse9025%40gmail.com
        current_url = driver.current_url
        time.sleep(5)
        if 'action' in current_url:
            time.sleep(15)
        time.sleep(10)
        if 'token' in driver.current_url:
            print('---- 登陆成功')
        else:
            print('---- 登陆失败')
        driver.get('https://mp.weixin.qq.com/') # reload for getting cookies
        time.sleep(5) # sleep for 5 seconds 
        cookies_items = driver.get_cookies()

        for cookie_item in cookies_items:
            post[cookie_item['name']] = cookie_item['value']
        cookie_str = json.dumps(post)
        with open('./../data/cookie.txt','w+', encoding='utf-8') as f:
            f.write(cookie_str)
        print('---- cookies 保存本地')
        driver.close()
        print('---- Crawler Closed.')
    except Exception as e:
        print(f'---- Error : {e} \n')
        traceback.print_exc()
        driver.close()
        print('---- Crawler Closed by error')

def get_content_param():
    header = {
        'HOST':'mp.weixin.qq.com',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    }
    with open('./../data/cookie.txt', 'r') as f:
        cookies = json.load(f)
    if not list(cookies.keys())[0].startswith('openid2ticket'):
        wechat_login()
    return header, cookies

def get_content_token(query, path, header, cookies):
    # query is the list of account that need to be crawled
    # index page
    url = 'https://mp.weixin.qq.com'
    # once login, the index page url becomes:
    # https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1060783525
    response = requests.get(url, cookies=cookies, headers=header)
    if response.status_code == '404':
        return get_content_token(query, path, header, cookies)
    try:
        token = re.findall(r'token=(\d+)', str(response.url))[0]
        print(f'---- {query} token get: {token}')
    except:
        print('------ Login fail')
        return 0
    return token

def get_content_fakeid(query, path, token, header, cookies):
    # search account api
    # https://mp.weixin.qq.com/cgi-bin/searchbiz?
        # action=search_biz
        # &token=575883549
        # &lang=zh_CN
        # &f=json
        # &ajax=1
        # &random=0.3131444494595672
        # &query=ifanr
        # &begin=0
        # &count=5
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    # search param
    search_param = {
        'action': 'search_biz',
        'token' : token,
        'lang'  : 'zh_CN',
        'f'     : 'json',
        'ajax'  : '1',
        'random': random.random(),
        'query' : query,
        'begin' : '0',
        'count' : '5'
    }
    # search
    search_response = requests.get(
        search_url, 
        cookies=cookies,
        # headers=header,
        params=search_param
    )
    try:
        lists = search_response.json().get('list')[0] # get the first account
        fakeid = lists.get('fakeid') # get the fakeid
        print(f'---- {query} fakeid get : {fakeid}')
    except:
        fakeid = 'fail'
    return fakeid

def get_content_msg(query, path, token, fakeid, header, cookies):
    # account msg api
    # https://mp.weixin.qq.com/cgi-bin/appmsg?
        # token=575883549
        # &lang=zh_CN
        # &f=json
        # &ajax=1
        # &random=0.011902100805929683
        # &action=list_ex
        # &begin=0
        # &count=5
        # &query=
        # &fakeid=MjgzMTAwODI0MA%3D%3D
        # &type=9
    appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    appmsg_param = {
        'token' : token,
        'lang'  : 'zh_CN',
        'f'     : 'json',
        'ajax'  : '1',
        'random': random.random(),
        'action': 'list_ex',
        'begin' : '0',
        'count' : '5',
        'query' : '',
        'fakeid': fakeid,
        'type'  : '9'
    }
    # search
    appmsg_response = requests.get(
        appmsg_url, 
        headers=header,
        params=appmsg_param,
        cookies=cookies
    )   
    print(f'---- Starting {query} msg:')
    appmsg_response_json = appmsg_response.json()
    try:
        max_num = appmsg_response_json.get('app_msg_cnt') # number of msg of this account
        num_page = int(int(max_num) / 5)
    except Exception as e:
        print(f'---- Get Msg list fail: {e}\n---- Error response: {appmsg_response.text}')
        return 0
    begin = 0
    for _ in range(num_page):
        appmsg_param = {
            'token' : token,
            'lang'  : 'zh_CN',
            'f'     : 'json',
            'ajax'  : '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin' : f'{begin}',
            'count' : '5',
            'query' : '',
            'fakeid': fakeid,
            'type'  : '9'
        }
        print(f'---- ---- 翻页中：「{query}」, Page: {begin}')
        # get link of each msg
        fakeid_response = requests.get(
            appmsg_url,
            cookies=cookies,
            params=appmsg_param,
            headers=header
        )
        fakeid_list = fakeid_response.json().get('app_msg_list')

        fileName = path + query + '.txt'
        with open(fileName, 'a+', encoding='utf-8') as f:
            json.dump(fakeid_list, f)
        begin = int(begin)
        begin += 5
        time.sleep(2)
    


if __name__ == '__main__':
    try:
        file_list = [f for f in listdir('./../data') if isfile(join('./../data', f))]
        if 'cookie.txt' not in file_list:
            wechat_login()
        path = './../data/account_file_list/'
        header, cookies = get_content_param()
        for query in gzlist:
            token = get_content_token(query, path, header, cookies)
            fakeid = get_content_fakeid(query, path, token, header, cookies)
            get_content_msg(query, path, token, fakeid, header, cookies)

        print('---- All done ----')
    except Exception as e:
        print(f'---- Error : {e}')
        traceback.print_exc()
        
