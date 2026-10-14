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
from pathlib import Path
import shutil


# 进阶版：批量读取 + 多种格式；增量更新；文件归档；删除失效chunk/source
class RAGPipeline:

    # 初始化：
    # 加载——切分——嵌入——存储 只做一次
    # 初始化检索器和Agent
    def __init__(self):
        logger.info("="*10 + "RAG初始化开始" + "="*10)
        # 1.加载
        loader = DocumentLoader() # 批量读取，多种格式
        doc_list_load = loader.load_all_files()

        # 2.切分
        splitter = TextSplitter() # 初始化切分器
        doc_list_split = splitter.splite_documents(doc_list_load) # 切分

        # 3.删除失效chunk，剔除旧chunk，返回新chunk
        vector_store = MilvusStore() # 连接Milvus数据库
        add_chunks = vector_store.delete_and_get(doc_list_split)

        # 不能等有数据要嵌入才初始化嵌入模型，要提前初始化，因为检索器那里也需要使用嵌入模型
        embed = Embedding() # 初始化嵌入模型
        # 如果有需要更新的数据存在才做嵌入与存储、归档
        if add_chunks:
            logger.info("开始进行数据更新")
            # 4.嵌入：只对新chunk做嵌入
            text_list,source_list = splitter.change_to_text_list(add_chunks) # 转化
            vector_list = embed.embed_documents(text_list) # 嵌入

            # 5.存储：只存储新chunk
            vector_store.upsert_vector(vector_list,text_list,source_list) # 存储

            # 6.对已经存储的文档进行归档（从source移动到target）
            logger.info("数据更新结束，开始进行文件归档")
            for relative_path in set(source_list): # set()去重，防止重复来源在move时报错（提示已存在）
                # 文件源路径：包括文件名
                start = Path(Setting.KNOWLEDGE_SOURCE_FOLDER_PATH) / Path(relative_path)
                # 文件归档路径：不需要文件名(.patent = 去除文件名的多级子目录)
                end = Path(Setting.KNOWLEDGE_TARGET_FOLDER_PATH) / Path(relative_path).parent
                # 自动创建路径，move对于不存在的路径会改文档名为最后一个路径
                end.mkdir(parents=True,exist_ok=True)
                # 移动归档
                shutil.move(start,end)
            logger.info("文件已完成归档")

        # 7.删除失效source
        # 先获取target目录下所有文件
        all_file_path = loader.get_all_file(Setting.KNOWLEDGE_TARGET_FOLDER_PATH)
        # 传入的路径要剔除target，只保留多级子目录+文档名
        file_list = []
        for file_path in all_file_path:
            file_list.append(
                str(
                    Path(file_path).relative_to(Setting.KNOWLEDGE_TARGET_FOLDER_PATH)
                )
            )
        # 与数据库对比，数据库有target目录没有的source就删除
        vector_store.detele_source(file_list)

        # 8.初始化检索器和Agent
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



































# # 基础版：只读一份txt；全量更新
# class RAGPipeline:

#     # 初始化：
#     # 加载——切分——嵌入——存储 只做一次
#     # 初始化检索器和Agent
#     def __init__(self):
#         logger.info("="*10 + "RAG初始化开始" + "="*10)
#         # 1.加载
#         loader = DocumentLoader() # 默认读取一份文件data/knowledge.txt
#         doc_list_load = loader.load()

#         # 2.切分
#         splitter = TextSplitter() # 初始化切分器
#         doc_list_split = splitter.splite_documents(doc_list_load) # 切分
#         text_list = splitter.change_to_text_list(doc_list_split) # 转化

#         # 3.嵌入
#         embed = Embedding() # 初始化嵌入模型
#         vector_list = embed.embed_documents(text_list) # 嵌入

#         # 4.存储
#         vector_store = MilvusStore() # 连接Milvus数据库
#         vector_store.upsert_vector(vector_list,text_list,Setting.KNOWLEDGE_FILE_PATH) # 存储

#         # 5.初始化检索器和Agent
#         self.retriever = Retriever(embed,vector_store) # 指明检索器使用的嵌入模型和数据库
#         self.agent = Agent()
#         logger.info("="*10 + "RAG初始化结束" + "="*10)

#     # 单次作答，在项目入口main.py中可使用while True进行循环作答
#     def ask(self,query):
#         # 问题转向量在检索器里已经实现，直接获取检索结果
#         context = self.retriever.retriever(query)
#         # 将查询结果作为上下文，结合用户提问一起给模型
#         answer = self.agent.answer(query,context)
#         return answer