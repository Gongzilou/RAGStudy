"""  
整体流程模块

RAG完整链路:
首先
加载文件——切分文件——嵌入文件——存储文件向量
接着
嵌入用户提问——数据库语义查询——Agent结合上下文和用户提问进行作答
"""

from config.settings import Setting
from core.agent import Agent
from core.document_loader import DocumentLoader
from core.embedding import Embedding
from core.retriever import Retriever
from core.text_splitter import TextSplitter
from core.vector_store import MilvusStore
from utils.logger import logger


class RAGPipeline:

    # 初始化：
    # 加载——切分——嵌入——存储 只做一次
    # 初始化检索器和Agent
    def __init__(self):
        logger.info("="*10 + "RAG初始化开始" + "="*10)
        # 1.加载
        loader = DocumentLoader() # 默认读取一份文件data/knowledge.txt
        doc_list_load = loader.load()

        # 2.切分
        splitter = TextSplitter() # 初始化切分器
        doc_list_split = splitter.splite_documents(doc_list_load) # 切分
        text_list = splitter.change_to_text_list(doc_list_split) # 转化

        # 3.嵌入
        embed = Embedding() # 初始化嵌入模型
        vector_list = embed.embed_documents(text_list) # 嵌入

        # 4.存储
        vector_store = MilvusStore() # 连接Milvus数据库
        vector_store.upsert_vector(vector_list,text_list,Setting.KNOWLEDGE_FILE_PATH) # 存储

        # 5.初始化检索器和Agent
        self.retriever = Retriever(embed,vector_store) # 指明检索器使用的嵌入模型和数据库
        self.agent = Agent()
        logger.info("="*10 + "RAG初始化结束" + "="*10)

    # 单次作答，在项目入口main.py中可使用while True进行循环作答
    def ask(self,query):
        # 问题转向量在检索器里已经实现，直接获取检索结果
        context = self.retriever.retriever(query)
        # 将查询结果作为上下文，结合用户提问一起给模型
        answer = self.agent.answer(query,context)
        return answer