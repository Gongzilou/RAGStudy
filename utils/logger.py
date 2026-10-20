"""  
日志工具模块

将日志记录在文档中，同时在终端也输出日志
"""

# 加入项目根目录，单跑文件模块时使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





import logging
import os

from config.settings import Setting
from datetime import datetime


def get_logger(name:str,log_file_path:str=Setting.LOG_FILE_PATH):
    """  
    定义一个具名logger,
    与root以及其他库的logger做命名空间隔离,
    便于做层级化控制日志级别和输出
    """
    # 1.先获取新logger
    logger = logging.getLogger(name)

    # 2.判断logger是否配置过handler,防止import时重复配置导致日志重复打印
    if logger.handlers:
        return logger

    # =====开始配置logger=====

    # 3.设置log等级
    # logger.setLevel(logging.INFO)
    # 五个等级：DEBUG、INFO、WARNING、ERROR、CRITICAL
    log_level = getattr(logging,Setting.LOG_LEVEL,logging.INFO)
    logger.setLevel(log_level)

    # 4.按格式打印：时间——logger名——等级——信息
    # logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # %：格式化操作符的开始；s：转成字符串，默认style="%"
    log_structured_output = logging.Formatter(
        "{asctime} - {name} - {levelname} - {message}",
        style="{"
    )

    # 5.输出：终端输出 + 文档输出

    # 5-1.终端输出
    log_stream = logging.StreamHandler() # 默认在终端输出
    log_stream.setFormatter(log_structured_output)
    logger.addHandler(log_stream)

    # 5-2.文档输出
    # 对传入的log_file_path做判断，
    # 只有文档名，则会存在运行目录下；
    # 有路径 + 文档名，则要先创建路径，否则logging.FileHandler()报错





    # # =====创建路径方式一（使用os）=====
    # # 获取要存文档的所在目录，只有文档名就获取空值""
    # file_path = os.path.dirname(log_file_path)
    # # 空值路径会让os.makedirs报错，所以做判断
    # if file_path:
    #     os.makedirs(file_path,exist_ok=True)


    # =====创建路径方式二（使用Path）=====
    # 1.先将路径字符串转为Path对象
    path = Path(log_file_path)
    # 2.直接调用mkdir
    # parents=True表示可以创建多级目录
    # exist_ok=True表示存在路径就跳过
    # 与os区别在于：无需判断空路径，当只有文件名时，此处不是空路径，是"."，表示当前路径；但因为当前路径存在，所以不会再创建
    
    
    
    
    # 不把log存一个文档里，按日期存不同log文档
    # path.parent.mkdir(parents=True,exist_ok=True)
    path.mkdir(parents=True,exist_ok=True)
    rel_log_file_path = f"{log_file_path}/{datetime.now():%Y%m%d}.log"



    
    
    log_file = logging.FileHandler(filename=rel_log_file_path,encoding="utf-8") # 文档输出
    log_file.setFormatter(log_structured_output)
    logger.addHandler(log_file)

    return logger

# 模块导出，其他文件直接import这个就行
logger = get_logger("RAGStudy")





if __name__ == "__main__":
    print(f"logger:\n{logger}")