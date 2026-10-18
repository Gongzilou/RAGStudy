"""  
检索模块

将用户提问向量化,
接着进行语义检索+BM25关键词检索,
然后将检索结果进行Rerank重排,
用重排后的结果重新组装成上下文,
后续会将上下文与用户提问一起提交给大模型进行回答
"""

# 加入根目录，单测文件时使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





from config.settings import Setting
from core.embedding import Embedding
from core.reranker import Reranker
from core.vector_store import MilvusStore
from utils.logger import logger


class Retriever:
    """  
    用户提问转向量 + 向量库检索 + 重排序 + 拼装上下文
    """
    # 加载嵌入模型和向量库、重排序器
    def __init__(self,embedding:Embedding,vector_store:MilvusStore,reranker:Reranker):
        self.embedding = embedding
        self.vector_store = vector_store
        self.reranker = reranker

    # 根据用户提问，检索指定数量的结果，返回拼装好的上下文
    def retriever(self,query:str,limit:int=Setting.RETRIEVER_TOP_K):
        # 1.问题转向量
        query_vector = self.embedding.embed_query(query)



        # 基础版
        # # 2.向量检索
        # result = self.vector_store.search(query_vector,limit)

        # # 检索进阶版1
        # # 2.向量检索 + BM25关键词检索（已经经过RRF粗排）
        # logger.info("开始进行双路检索")
        # result = self.vector_store.search(query,query_vector,limit)
        # logger.info("双路检索结束")

        # 检索进阶版2
        # 2.向量检索 + BM25关键词检索
        logger.info("开始进行双路检索")
        recall_result = self.vector_store.search(query,query_vector)
        logger.info("双路检索结束")
        # 3.将检索结果进行重排序（使用模型为：BAAI/bge-reranker-v2-m3）
        result = self.reranker.rerank(query,recall_result,limit)



        # 4.拼装上下文（将返回的结果格式化后拼成一大段字符串，中间以段落相隔）
        context_block = []
        for i,row in enumerate(result,1):
            id = row["id"]
            distance = row["distance"] # 距离
            text = row["entity"].get("text","unknow") # 原文
            source = row["entity"].get("source","unknow") # 来源
            context_block.append(
                f"[片段{i} | id={id} | distance={distance} | source={source}]\n{text}"
            )
        context = "\n\n".join(context_block)
        logger.info(f"检索完成，召回{len(result)}条数据")
        return context





if __name__ == "__main__":
    embedding = Embedding()
    vector_store = MilvusStore()
    retriever = Retriever(embedding,vector_store)
    query = "测试问题"
    limit = 3
    result = retriever.retriever(query,limit)
    print(f"结果：\n{result}")
        