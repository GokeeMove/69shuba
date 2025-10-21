# -*- coding: utf-8 -*-


from lxml import etree
from urllib.request import urlopen
import re
import time
import multiprocessing
from multiprocessing import Pool
import aiohttp
import asyncio

urls = [] #储存各章节的URL
htmls = {}#储存各章节页面HTML
nums = []
titles = []#储存各章节名字
book=""
process_num = 0 #进程数，一般范围为CPU内核数到50
sem = asyncio.Semaphore(40) # 信号量，控制协程数，防止爬的过快

def getText(base_url, til_url):
    global book
    repons = urlopen(base_url + til_url)
    tree = etree.HTML(repons.read())
    book = tree.xpath('//title')[0].text
    dd = tree.xpath('//dd/a[@href]')
    i=1
    for di in dd:
        urls.append(base_url+di.attrib.get('href'))
        titles.append(di.text)
        nums.append(i)
        i=i+1


def getContent():
    global book
    htmls2= [(k,htmls[k]) for k in sorted(htmls.keys())]
    tfile = open("./fictions/" + book + ".txt", 'a')
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
    with(await sem):#等待其中20个协程结束才进行下一步
        # async with是异步上下文管理器
        async with aiohttp.ClientSession() as session:  # 获取session
            async with session.request('GET', url) as resp:  # 提出请求
                start = time.time()
                html = await resp.text() # 直接获取到bytes
                print('获取耗时：%.5f秒' % float(time.time()-start))
                start = time.time()
                tree = etree.HTML(html)
                pptitle = tree.xpath('//title')[0].text
                content = tree.xpath('//div[@id="content"]/text()')
                txt = ''
                for i in range(len(content)):
                    txt = txt+content[i].strip()+'\n'   # strip()去掉首位空格字符，‘\n’换行
                    #txt = txt.replace('笔趣阁TV手机端https://m.biqugetv.com/','')
                htmls[num]="\n\n\n" + pptitle + "\n"+ str(txt)
                print('解析耗时：%.5f秒' % float(time.time()-start))
                print("获取及解析"+pptitle)
                
def download_path(path_url):
    print("path---->"+path_url)
    getText("https://www.biquge.com.cn", path_url)
    start = time.time()
    main_get_html()
    print('获取及解析耗时：%.5f秒' % float(time.time()-start))
    start = time.time()
    getContent()
    print('写入耗时：%.5f秒' % float(time.time()-start))
    
download_path("/book/44060/")
# getText("https://www.biquge.com.cn", "/book/44060/")
