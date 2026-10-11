"""  
嵌入模块

使用硅基流动平台的BAAI/bge-m3嵌入模型
"""

# 添加项目根目录，单跑文件测试时使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





from langchain.embeddings import init_embeddings

from config.settings import Setting
from utils.logger import logger


class Embedding:
    """  
    初始化嵌入模型 + 文本转向量 + 问题转向量
    """
    def __init__(self):
        # 初始化嵌入模型：BAAI/bge-m3
        try:
            self.model = init_embeddings(
                # model="openai:" + Setting.EMBED_MODEL,
                model=Setting.EMBED_MODEL,
                provider=Setting.EMBED_MODEL_PROVIDER,
                api_key=Setting.EMBED_API_KEY,
                base_url=Setting.EMBED_BASE_URL,
            )
            logger.info("嵌入模型初始化成功")
        except Exception as e:
            logger.error(f"嵌入模型初始化失败：\n{e}")
            raise

    def embed_documents(self,text_list):
        # 将文本列表转为向量列表
        vector_list = self.model.embed_documents(text_list)
        logger.info(f"文本嵌入成功：{len(vector_list)}条")
        return vector_list

    def embed_query(self,query):
        # 将用户的单个查询转成向量
        logger.info("用户提问嵌入完成")
        return self.model.embed_query(query)





if __name__ == "__main__":
    texts = [
        "测试1",
        "测试2",
        "测试3"
    ]
    query = "什么问题？"
    embedding = Embedding()
    vectors = embedding.embed_documents(texts)
    for i,vector in enumerate(vectors):
        print(f"{texts[i]} : {vector[:3]}")
    q_ve = embedding.embed_query(query)
    print(f"{query} : {q_ve[:3]}")