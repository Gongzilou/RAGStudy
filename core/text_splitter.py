"""  
文档切分模块

使用递归切分器: RecursiveCharacterTextSplitter
目前支持切分方式: split.document()
"""

# 加入项目根目录，单跑文件测试使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Setting
from utils.logger import logger


class TextSplitter:
    """  
    使用递归切分器

    切分方式: split.document()
    传入: document对象列表
    传出: document对象列表

    最后从document对象列表提取所有内容page_content,
    转成字符串列表,便于后续转向量
    """
    # 初始化递归切分器
    def __init__(self):
        try:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=Setting.CHUNK_SIZE,
                chunk_overlap=Setting.CHUNK_OVERLAP,
                separators=[
                    "\n# ", # md文档一级标题
                    "\n## ", # md文档二级标题
                    "==============================",
                    "\n\n",
                    "\n",
                    "。", "！", "？", "；",
                    "，",
                    " ",
                    ""
                ],
            )
            logger.info("递归切分器初始化成功")
        except Exception as e:
            logger.error(f"递归切分器初始化失败：\n{e}")
            raise

    # 切分文档
    def splite_documents(self,docs):
        # 先判断要切分的文档是否存在
        if not docs:
            logger.warning(f"没发现需要切分的文档")
            return []
        # 切分
        chunks = self.splitter.split_documents(docs)
        logger.info(f"已将文档切分为{len(chunks)}块")
        return chunks

    # 转化
    def change_to_text_list(self,chunks):
        # 从处理好的chunks（已剔除数据库存在的chunk）中提取所有page_content,
        # 转为字符串列表,
        # 便于后续做向量化，
        # 同时记录对应来源——子目录+文档名（不再从setting获取，那里只记录目录路径）
        text_list = [
            doc.page_content for doc in chunks
        ]
        source_list = [
            doc.metadata["source"] for doc in chunks
        ]
        # logger.info("切好的文档已转换为字符串列表，后续可以直接做嵌入处理")
        return text_list,source_list





if __name__ == "__main__":
    from core.document_loader import DocumentLoader
    loader = DocumentLoader()
    # docs = loader.load()
    docs = loader.load_all_files()
    splitter = TextSplitter()
    chunks = splitter.splite_documents(docs)
    text_list = splitter.change_to_text_list(chunks)
    print(f"text_list:\n{text_list}")