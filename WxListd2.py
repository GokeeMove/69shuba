# -*- coding: utf-8 -*-


from lxml import etree
from urllib.request import urlopen
import urllib.request
import re
import requests
import time
import multiprocessing
from multiprocessing import Pool
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import aiohttp
import asyncio
import ssl

urls = [] #储存各章节的URL
htmls = {}#储存各章节页面HTML
nums = []
titles = []#储存各章节名字
book=""
process_num = 4#进程数，一般范围为CPU内核数到50
sem = asyncio.Semaphore(40) # 信号量，控制协程数，防止爬的过快

headers = {
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
  'accept-language': 'zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7',
  'cache-control': 'max-age=0',
  'if-modified-since': 'Tue, 08 Jul 2025 04:25:34 GMT',
  'if-none-match': '"cb1c5ad8f67388d6f7184a58552b8625"',
  'priority': 'u=0, i',
  'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"',
  'sec-fetch-dest': 'document',
  'sec-fetch-mode': 'navigate',
  'sec-fetch-site': 'none',
  'sec-fetch-user': '?1',
  'upgrade-insecure-requests': '1',  
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
  'Cookie': 'zh_choose=s; cf_clearance=prd5HPFf3QPClIiSKYnfh0Oyusq6KQQzSpxUYogd3IA-1761047032-1.2.1.1-dT2vR2vRS3KJmex0vESSsxVgo4E88cJzfmMXITeskVZY8iDHPHoILdv2ruTAZufbbXsdVhj2AWTEpU3fe2UBMKVwdK39rI.dVDcKJeugUB__Pf5pw0TJD7qUMRZgvWhxNzfOrjWUulAqs5uSbxl6NJxAVo7Tfj9cW35LNo2rjKcmgl_OVtYPIOZB.10jAmL.Mbbx1AFntxQoocSpw1RHrTQZb5A4kpzT9sAiUNVBL38; shuba_userverfiy=1761047032@35ffb5e91af7702379bba3560f8f5e18; jieqiVisitTime=jieqiArticlesearchTime%3D1761047033; shuba=11415-10492-23399-5789; _ga=GA1.1.2032785226.1761047035; _ga_04LTEL5PWY=GS2.1.s1761047035$o1$g1$t1761047039$j56$l0$h0',
  'If-Modified-Since': 'None',
  'If-None-Match': 'None'
}


payload = {}

class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block)

def getText(base_url, til_url):
    global book
    s=requests.Session()
    s.mount('https://', MyAdapter())
    # req=urllib.request.Request("GET",url=base_url + til_url, headers=headers, data=payload)
    # repons = urlopen(req)
    repons = requests.request("GET", url=base_url + til_url, headers=headers, data=payload)
    tree = etree.HTML(repons.text)
    book = tree.xpath('//title')[0].text
    print("title->"+book)
    dd = tree.xpath('//*[@id="catalog"]/ul/li/a[@href]')
    i=len(dd)
    for di in dd:
        urls.append(di.attrib.get('href'))
        resp = requests.request("GET", url=di.attrib.get('href'), headers=headers, data=payload)
        tree = etree.HTML(resp.text)
        pptitle = tree.xpath('//title')[0].text
        content = tree.xpath('/html/body/div[2]/div[1]/div[3]/text()')
        txt = ''
        for j in range(len(content)):
            txt = txt+content[j].strip()+'\n'   # strip()去掉首位空格字符，‘\n’换行
            #txt = txt.replace('笔趣阁TV手机端https://m.biqugetv.com/','')
        htmls[i]="\n\n\n" + pptitle + "\n"+ str(txt)
        # print('解析耗时：%.5f秒' % float(time.time()-start))
        print("complete->"+str(pptitle))
        titles.append(di.text)
        nums.append(i)
        i=i-1


def getContent():
    global book
    htmls2= [(k,htmls[k]) for k in sorted(htmls.keys())]
    tfile = open("/root/python_fiction/fictions/" + book + ".txt", 'a')
    print(tfile)
    for content in htmls2:
        tfile.write(str(content[1]))
    tfile.close()

    '''
协程调用方，作用：请求网页
'''
def main_get_html():
    loop = asyncio.get_event_loop()           # 获取事件循环
    tasks = [get_html(num,url,title) for num,url,title in zip(nums,urls,titles)]  # 把所有任务放到一个列表中
    loop.run_until_complete(asyncio.wait(tasks)) # 激活协程
    loop.close()  # 关闭事件循环

    #——————————————————————————————————————————————————#
'''                                                                                                 
提交请求获取网页html                                                                            
'''
async def get_html(num,url,title):
    async with sem:#等待其中20个协程结束才进行下一步
        # async with是异步上下文管理器
        max_retries = 3  # 最大重试次数
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with aiohttp.ClientSession() as session:  # 获取session
                    async with session.request('GET', url, headers=headers, data=payload) as resp:  # 提出请求
                        start = time.time()
                        
                        # 检查响应状态码
                        if resp.status == 304:
                            print(f"收到304状态码，第{retry_count + 1}次重试...")
                            retry_count += 1
                            if retry_count < max_retries:
                                await asyncio.sleep(1)  # 等待1秒后重试
                                continue
                            else:
                                print(f"重试{max_retries}次后仍然收到304，跳过此章节: {title}")
                                return
                        
                        html = await resp.text(encoding='gbk') # 直接获取到bytes
                        print("html->"+str(html))
                        start = time.time()
                        tree = etree.HTML(html)
                        pptitle = tree.xpath('//title')[0].text
                        content = tree.xpath('/html/body/div[2]/div[1]/div[3]/text()')
                        txt = ''
                        for i in range(len(content)):
                            txt = txt+content[i].strip()+'\n'   # strip()去掉首位空格字符，'\n'换行
                            #txt = txt.replace('笔趣阁TV手机端https://m.biqugetv.com/','')
                        htmls[num]="\n\n\n" + pptitle + "\n"+ str(txt)
                        # print('解析耗时：%.5f秒' % float(time.time()-start))
                        print("complete->"+str(pptitle))
                        return  # 成功获取内容，退出重试循环
                        
            except Exception as e:
                print(f"请求出错: {e}, 第{retry_count + 1}次重试...")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # 等待2秒后重试
                else:
                    print(f"重试{max_retries}次后仍然失败，跳过此章节: {title}")
                    return
                
def download_path(path_url):
    print("path---->https://www.69shuba.com"+path_url)
    getText("https://www.69shuba.com", path_url)
    start = time.time()
    # main_get_html()
    print('获取及解析耗时：%.5f秒' % float(time.time()-start))
    start = time.time()
    getContent()
    print('写入耗时：%.5f秒' % float(time.time()-start))
    
start_time = time.time()
download_path("/book/90072/")
print('耗时：%.5f秒' % float(time.time()-start_time))
# getText("https://www.biquge.com.cn", "/book/90072/")
