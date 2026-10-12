"""  
文档加载模块

目前支持加载格式：
    1.txt文档
"""

# 加入项目根目录，单跑文件测试模块时使用，防止找不到其他路径的导入包
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))





import os

from langchain_community.document_loaders import TextLoader

from config.settings import Setting
from utils.logger import logger


class DocumentLoader:
    """  
    将知识库文件加载为document列表

    目前支持加载方式：
        TextLoader()
    """
    # 获取文件路径
    def __init__(self,file_path:str=Setting.KNOWLEDGE_FILE_PATH):
        self.file_path = file_path

    # 加载文件
    def load(self)->list:
        # 先判断文件是否存在
        if not Path(self.file_path).exists(): # Path对象方式
        # if not os.path.exists(self.file_path): # os方式
            logger.error(f"知识库文件{self.file_path}不存在")
            raise FileNotFoundError(
                f"知识库文件【{self.file_path}】不存在\n"
                "请确认文件是否放入data/目录下，"
                "或者文件路径是否配置正确"
            )
        loader = TextLoader(
            file_path=self.file_path,
            encoding="utf-8"
        )
        document_list = loader.load()
        # 记录来源，后续会新增功能“答案溯源”
        # 部分文档加载器不会自带source字段
        for doc in document_list:
            if "source" not in doc.metadata:
                doc.metadata["source"] = self.file_path

        logger.info(f"知识库文档{self.file_path}已加载完成")

        return document_list





# 单跑文件测试模块
if __name__ == "__main__":
    loader = DocumentLoader()
    docs = loader.load()
    print(f"docs:\n{docs}")