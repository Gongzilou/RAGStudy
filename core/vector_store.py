"""  
向量数据库模块

使用Docker + Milvus
"""

# 加入根目录，单测文件使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





from pymilvus import MilvusClient

from config.settings import Setting
from utils.logger import logger


class MilvusStore:
    """ 
    先通过Docker Desktop启动Milvus

    创建客户端对象,
    连接Milvus服务端,
    然后建库、建集合、存储、查询
    """
    def __init__(self):
        # 初始化参数

        # 创建客户端对象: MilvusClient，
        # 连接Milvus服务端: uri
        try:
            self.client = MilvusClient(
                uri=Setting.MILVUS_URL,
                timeout=10 # 主动设置超时时间，没启动服务原本会连接很久
            )
            logger.info(f"Milvus服务端{Setting.MILVUS_URL}连接成功")
        except Exception as e:
            logger.error(f"Milvus服务端{Setting.MILVUS_URL}连接失败：\n{e}")
            raise

        self.db_name = Setting.MILVUS_DB_NAME
        self.collection_name = Setting.MILVUS_COLLECTION
        self.embed_dimension = Setting.EMBED_DIMENSION
        # 建库和集合
        try:
            self.create_database_and_collection()
            logger.info("Milvus数据库连接成功")
        except Exception as e:
            logger.error(f"Milvus数据库连接失败：\n{e}")
            raise

    def create_database_and_collection(self):
        # 创建数据库和集合

        # 创建数据库，先查询，没有就创建
        databases = self.client.list_databases()
        if self.db_name not in databases:
            self.client.create_database(db_name=self.db_name)
            logger.info(f"数据库{self.db_name}创建成功")
        else:
            logger.info(f"数据库{self.db_name}已存在")
            logger.info(f"当前所有数据库：\n{databases}")
        
        # 切换到创建的数据库进行使用
        self.client.use_database(db_name=self.db_name)

        # 创建集合，先查询，没有就创建
        collections = self.client.list_collections()
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=self.embed_dimension,
                metric_type="COSINE"
            )
            logger.info(f"集合{self.collection_name}创建成功")
        else:
            logger.info(f"集合{self.collection_name}已存在")
            logger.info(f"当前数据库{self.db_name}的所有集合：\n{collections}")

    def upsert_vector(self,vector_list,text_list,source):
        # 将向量数据存进数据库集合中

        # 先将向量列表构造成新数据：向量 + 文本 + 来源
        data_list = [
            {
                "id":i,
                "vector":vector,
                "text":text_list[i],
                "source":source
            } for i,vector in enumerate(vector_list)
        ]
        # 将数据存入集合
        result = self.client.upsert(
            collection_name=self.collection_name,
            data=data_list
        )
        logger.info(f"已存入{len(data_list)}条数据：\n{result}")

    def search(self,query_vector,limit):
        # 根据用户提问，查询最接近的几条结果
        # 包含id、distance、entity中的text和source

        result = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector], # 包装成二维的
            limit=limit,
            output_fields=["text","source"]
        )
        return result[0] # 二维的





if __name__ == "__main__":
    milvus_store = MilvusStore()
    print(f"初始化：\n{milvus_store}")