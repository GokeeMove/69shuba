# -*- coding: utf-8 -*-
"""
调试配置文件
用于配置小说爬虫的调试选项
"""

# 调试模式配置
DEBUG_CONFIG = {
    # 是否开启调试模式
    'debug_mode': True,
    
    # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_level': 'DEBUG',
    
    # 是否保存日志到文件
    'save_log_to_file': True,
    
    # 是否显示详细的请求信息
    'show_request_details': True,
    
    # 是否显示性能统计
    'show_performance_stats': True,
    
    # 是否在每10个章节后显示进度
    'show_progress_every_n': 10,
    
    # 是否显示章节内容长度
    'show_content_length': True,
    
    # 是否在错误时显示完整堆栈跟踪
    'show_full_traceback': True,
    
    # 是否保存失败的章节URL到文件
    'save_failed_urls': True,
    
    # 是否显示网络连接详情
    'show_connection_details': False,
}

# 性能监控配置
PERFORMANCE_CONFIG = {
    # 是否启用性能监控
    'enable_performance_monitoring': True,
    
    # 是否记录每个请求的详细时间
    'record_detailed_timing': True,
    
    # 是否在控制台显示实时统计
    'show_realtime_stats': True,
    
    # 性能报告保存路径
    'performance_report_path': './performance_report.txt',
}

# 网络配置
NETWORK_CONFIG = {
    # 请求超时时间（秒）
    'request_timeout': 30,
    
    # 连接超时时间（秒）
    'connect_timeout': 10,
    
    # 最大重试次数
    'max_retries': 3,
    
    # 协程并发数
    'max_concurrent_requests': 50,
    
    # 连接池大小
    'connection_pool_size': 100,
    
    # 每个主机的最大连接数
    'max_connections_per_host': 30,
}

def get_debug_config():
    """获取调试配置"""
    return DEBUG_CONFIG

def get_performance_config():
    """获取性能配置"""
    return PERFORMANCE_CONFIG

def get_network_config():
    """获取网络配置"""
    return NETWORK_CONFIG

def print_config():
    """打印当前配置"""
    print("=" * 50)
    print("调试配置:")
    for key, value in DEBUG_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\n性能配置:")
    for key, value in PERFORMANCE_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\n网络配置:")
    for key, value in NETWORK_CONFIG.items():
        print(f"  {key}: {value}")
    print("=" * 50)

if __name__ == "__main__":
    print_config()
