# -*- coding: utf-8 -*-

import logging
import sys
import traceback
from datetime import datetime
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

# 调试配置
DEBUG_MODE = True  # 调试模式开关
LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO

# 配置日志
def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 创建logger
    logger = logging.getLogger('novel_crawler')
    logger.setLevel(LOG_LEVEL)
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(f'crawler_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 
                                      encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志
logger = setup_logging()

# 性能统计
class PerformanceStats:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_request_time = 0
        self.total_parse_time = 0
        
    def start_timing(self):
        self.start_time = time.time()
        logger.info("开始性能统计")
        
    def end_timing(self):
        self.end_time = time.time()
        logger.info("结束性能统计")
        
    def add_request(self, request_time, parse_time, success=True):
        self.request_count += 1
        self.total_request_time += request_time
        self.total_parse_time += parse_time
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            
    def get_stats(self):
        if self.start_time and self.end_time:
            total_time = self.end_time - self.start_time
            avg_request_time = self.total_request_time / self.request_count if self.request_count > 0 else 0
            avg_parse_time = self.total_parse_time / self.request_count if self.request_count > 0 else 0
            
            return {
                'total_time': total_time,
                'request_count': self.request_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'success_rate': self.success_count / self.request_count if self.request_count > 0 else 0,
                'avg_request_time': avg_request_time,
                'avg_parse_time': avg_parse_time
            }
        return {}

# 全局性能统计对象
stats = PerformanceStats()

urls = [] #储存各章节的URL
htmls = {}#储存各章节页面HTML
nums = []
titles = []#储存各章节名字
book=""
process_num = 4#进程数，一般范围为CPU内核数到50
sem = asyncio.Semaphore(50) # 信号量，控制协程数，防止爬的过快

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
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
  'Cookie': 'zh_choose=s; _ga=GA1.1.1229577024.1759026544; _cc_id=b8965d05e8809471ae03a0ead99d6f13; panoramaId_expiry=1761214652681; panoramaId=1155962b5cd92995387ec9fae8c316d539384c0122ce3de4974fddcef34e1408; panoramaIdType=panoIndiv; connectId={"ttl":86400000,"lastUsed":1761036005408,"lastSynced":1761036005408}; cto_bundle=t8kQK19xZExwVFhQSlFLT2p0dTBoZTI1cmxxVmcxN0t4eFZkOTA3ZTdWYzR5cEZLVVJzRCUyQklobm5GSHpDbEJMbUNtJTJGdTJKbmZIQXJhSTFIUENkZHROQVh0WEtiaDBPV1RtYmRUU0tCRkx5dWtlVSUyRjMwaHJQb1BGdVNYQ0ZaY3IxYVB2NVRsJTJCTmtYOTNrcW9DNXR4b01uVSUyRkIlMkZSeXdnZGo4UzBEQk5vbHV3WDZBdWZEeGtLa0c3aTQ4Um5ONjdVTU5FJTJCVU9NOFpCQ0tSZHNIUmRBS0MlMkY1clk2USUzRCUzRA; cf_clearance=66ndNK5w2t_gViVzNB41Apg_byKOq.sz6yPd9XSA5sg-1761045200-1.2.1.1-5knbAkTG5WgXfGvUb3g5wYXCvmFD3KC5Vxch6ugGX9fh433SYIbuYlIi6Sr3Wd7Tz8VDDcsKg_VVRyz_r4M3wwKFL7_nzyRAPzD._RQaXPREFr5xQDjOXTnJnXCH0q8sxamkvXmt_qqZj_F8TcTh.IWPwicbN7Y2MD5qwPbnUk2JQ6sXzpf6mXdceL8bkVkonbCKhTR44HADd_uUCjU2LZmpgQk8qbmk6Gh24QWtBic; shuba_userverfiy=1761045201@69a31ac58074120384a888e39c4ec60e; jieqiVisitTime=jieqiArticlesearchTime%3D1761045201; _ga_04LTEL5PWY=GS2.1.s1761045204$o5$g1$t1761045304$j59$l0$h0; shuba=8864-6805-19885-2275',
  'If-Modified-Since': 'None',
  'If-None-Match': 'None'
}


# 为异步请求创建headers2
headers2 = headers.copy()

payload = {}

class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            retries=3,  # 添加重试
            timeout=30  # 添加超时
        )

def getText(base_url, til_url):
    global book
    logger.info(f"开始获取书籍信息: {base_url}{til_url}")
    
    try:
        s = requests.Session()
        s.mount('https://', MyAdapter())
        
        logger.debug(f"发送请求到: {base_url + til_url}")
        repons = requests.request("GET", url=base_url + til_url, headers=headers, data=payload)
        
        if repons.status_code != 200:
            logger.error(f"请求失败，状态码: {repons.status_code}")
            raise Exception(f"HTTP请求失败: {repons.status_code}")
            
        logger.debug(f"请求成功，响应长度: {len(repons.text)} 字符")
        
        tree = etree.HTML(repons.text)
        book = tree.xpath('//title')[0].text
        logger.info(f"书籍标题: {book}")
        
        dd = tree.xpath('//*[@id="catalog"]/ul/li/a[@href]')
        logger.info(f"发现 {len(dd)} 个章节")
        
        if len(dd) == 0:
            logger.warning("未找到章节链接，可能页面结构发生变化")
            return False
        
        # 只收集URL，不立即请求内容
        i = len(dd)
        for di in dd:
            href = di.attrib.get('href')
            title = di.text
            if href and title:
                urls.append(href)
                titles.append(title)
                nums.append(i)
                i = i - 1
                logger.debug(f"添加章节 {i}: {title} -> {href}")
        
        logger.info(f"章节列表收集完成，共 {len(urls)} 个章节，开始异步获取内容...")
        return True
        
    except Exception as e:
        logger.error(f"获取书籍信息失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False


def getContent():
    global book
    logger.info("开始保存内容到文件")
    
    try:
        if not book:
            logger.error("书籍标题为空，无法保存文件")
            return False
            
        htmls2 = [(k, htmls[k]) for k in sorted(htmls.keys())]
        filename = f"./fictions/{book}.txt"
        
        logger.debug(f"准备写入文件: {filename}")
        logger.debug(f"共有 {len(htmls2)} 个章节需要保存")
        
        with open(filename, 'w', encoding='utf-8') as tfile:
            for i, content in enumerate(htmls2):
                tfile.write(str(content[1]))
                if DEBUG_MODE and i % 10 == 0:
                    logger.debug(f"已保存 {i+1}/{len(htmls2)} 个章节")
        
        logger.info(f"内容保存完成: {filename}")
        logger.info(f"文件大小: {len(str(htmls2))} 字符")
        return True
        
    except Exception as e:
        logger.error(f"保存内容失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

    '''
协程调用方，作用：请求网页
'''
def main_get_html():
    logger.info("开始异步获取章节内容")
    stats.start_timing()
    
    try:
        loop = asyncio.get_event_loop()           # 获取事件循环
        tasks = [get_html(num,url,title) for num,url,title in zip(nums,urls,titles)]  # 把所有任务放到一个列表中
        logger.info(f"开始异步获取 {len(tasks)} 个章节...")
        
        # 使用gather获得更好性能
        results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        
        # 统计结果
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        
        logger.info(f"章节获取完成: 成功 {success_count}, 失败 {error_count}")
        
        if error_count > 0:
            logger.warning(f"有 {error_count} 个章节获取失败")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"章节 {i+1} 获取失败: {str(result)}")
        
        loop.close()  # 关闭事件循环
        stats.end_timing()
        
    except Exception as e:
        logger.error(f"异步获取章节失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        stats.end_timing()

    #——————————————————————————————————————————————————#
'''                                                                                                 
提交请求获取网页html                                                                            
'''
async def get_html(num, url, title):
    logger.debug(f"开始获取章节 {num}: {title}")
    
    async with sem:  # 等待其中50个协程结束才进行下一步
        # 优化的连接器配置
        connector = aiohttp.TCPConnector(
            limit=100,  # 总连接池大小
            limit_per_host=30,  # 每个主机的连接数
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:  # 获取session
            try:
                logger.debug(f"发送请求到: {url}")
                async with session.request('GET', url, headers=headers2, data=payload) as resp:  # 提出请求
                    if resp.status != 200:
                        logger.warning(f"章节 {num} 请求失败，状态码: {resp.status}")
                        raise Exception(f"HTTP请求失败: {resp.status}")
                    
                    start = time.time()
                    html = await resp.text(encoding='gbk')  # 直接获取到bytes
                    request_time = time.time() - start
                    
                    logger.debug(f"章节 {num} 请求成功，响应长度: {len(html)} 字符")
                    
                    start = time.time()
                    tree = etree.HTML(html)
                    pptitle = tree.xpath('//title')[0].text
                    content = tree.xpath('/html/body/div[2]/div[1]/div[3]/text()')
                    
                    if not content:
                        logger.warning(f"章节 {num} 未找到内容，可能页面结构发生变化")
                        content = [f"章节 {num} 内容获取失败"]
                    
                    txt = ''
                    for i in range(len(content)):
                        txt = txt + content[i].strip() + '\n'   # strip()去掉首位空格字符，'\n'换行
                    
                    htmls[num] = "\n\n\n" + pptitle + "\n" + str(txt)
                    
                    parse_time = time.time() - start
                    
                    # 记录性能统计
                    stats.add_request(request_time, parse_time, success=True)
                    
                    logger.info(f"章节 {num} 完成 - 获取耗时: {request_time:.3f}秒, 解析耗时: {parse_time:.3f}秒 - {pptitle}")
                    
            except Exception as e:
                logger.error(f"获取章节 {num} 失败 {url}: {str(e)}")
                logger.debug(f"章节 {num} 错误详情: {traceback.format_exc()}")
                
                # 记录失败的统计
                stats.add_request(0, 0, success=False)
                
                htmls[num] = f"\n\n\n错误章节 {num}\n获取失败: {str(e)}\n"
                
def download_path(path_url):
    logger.info(f"开始下载路径: https://www.69shuba.com{path_url}")
    
    try:
        # 获取书籍信息
        if not getText("https://www.69shuba.com", path_url):
            logger.error("获取书籍信息失败，终止下载")
            return False
        
        # 异步获取章节内容
        start = time.time()
        main_get_html()  # 启用异步获取
        fetch_time = time.time() - start
        logger.info(f'获取及解析耗时：{fetch_time:.5f}秒')
        
        # 保存内容
        start = time.time()
        if not getContent():
            logger.error("保存内容失败")
            return False
        save_time = time.time() - start
        logger.info(f'写入耗时：{save_time:.5f}秒')
        
        # 输出性能统计
        performance_stats = stats.get_stats()
        if performance_stats:
            logger.info("=" * 50)
            logger.info("性能统计报告:")
            logger.info(f"总耗时: {performance_stats['total_time']:.3f}秒")
            logger.info(f"请求总数: {performance_stats['request_count']}")
            logger.info(f"成功数: {performance_stats['success_count']}")
            logger.info(f"失败数: {performance_stats['error_count']}")
            logger.info(f"成功率: {performance_stats['success_rate']:.2%}")
            logger.info(f"平均请求时间: {performance_stats['avg_request_time']:.3f}秒")
            logger.info(f"平均解析时间: {performance_stats['avg_parse_time']:.3f}秒")
            logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"下载过程失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False
    
# 主程序入口
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("小说爬虫程序启动")
    logger.info(f"调试模式: {'开启' if DEBUG_MODE else '关闭'}")
    logger.info("=" * 50)
    
    start_time = time.time()
    
    try:
        # 执行下载
        success = download_path("/book/30978/")
        
        total_time = time.time() - start_time
        logger.info("=" * 50)
        logger.info(f'程序总耗时：{total_time:.3f}秒')
        
        if success and len(htmls) > 0:
            avg_time = total_time / len(htmls)
            logger.info(f'平均每章节耗时：{avg_time:.3f}秒')
            logger.info(f'成功获取章节数：{len(htmls)}')
        else:
            logger.error("程序执行失败")
            
        logger.info("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
    except Exception as e:
        logger.error(f"程序执行异常: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
    finally:
        logger.info("程序结束")
