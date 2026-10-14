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
import hashlib


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










    # 进阶版：删除孤儿chunk（文档被改） + 增量更新 + 删除失效source（文档被删）
    # 先删除数据库有但文档没有的chunk（孤儿chunk），
    # 再新增数据库没有但文档有的部分新chunk，
    # 最后判断有没有被删的文档，有的话在数据库删除该source下所有chunk
    # 指纹：主键是chunk.source + chunk.page_content构成的hash值，再转成int64类型做id

    # 用哈希md5（32位）获取指纹；也可以用哈希SHA256，但它更长64位
    def get_fingerprint(self,source,content):
        row = f"{source}\x00{content}"
        fingerprint = hashlib.md5(row.encode("utf-8")).hexdigest()
        # 因为存的是int64整型id——十进制；取十六进制的哈希值前15位，1位哈希值=4bit
        # int64正数上限是2^63-1；15位哈希=60bit，最大是2^60-1；16位哈希最大是2^64-1
        return int(fingerprint[:15],16)

    # 传入刚切好的chunks
    # 删除数据库有但chunks没有的孤儿chunk
    # 返回数据库没有但chunks有的新增chunk，只对这部分做嵌入
    def delete_and_get(self,chunks):
        # chunks所有来源，用于找出来源下所有id
        all_source = [chunk.metadata["source"] for chunk in chunks]
        # 指纹 = 【来源 + 内容】的哈希值，用于删除孤儿chunk
        all_id = [
            self.get_fingerprint(chunk.metadata["source"],chunk.page_content)
            for chunk in chunks
        ]

        # 1.先找出数据库source下所有id
        result = self.client.query(
            collection_name=self.collection_name,
            filter=f"source in {list(set(all_source))}", # set()集合去重，in 后面接列表
            output_fields=["id"]
        )
        db_id = [row["id"] for row in result]

        # 2.删除孤儿chunk
        delete_id = set(db_id) - set(all_id)
        if delete_id:
            self.client.delete(
                collection_name=self.collection_name,
                ids=list(delete_id) # 集合转列表
            )
            logger.info(f"已删除失效片段：{len(delete_id)}条")
        else:
            logger.info("目前没有失效片段")

        # 3.返回数据库没有但chunks存在的新增chunk，只对这部分做嵌入，节省token
        add_chunks = [
            chunk
            for chunk in chunks
            if self.get_fingerprint(chunk.metadata["source"],chunk.page_content) not in set(db_id)
        ]
        logger.info(f"有{len(add_chunks)}条数据需要更新")
        return add_chunks

    # 对处理完的add_chunks做新增
    def upsert_vector(self,vector_list,content_list,source_list):
        # 将向量数据存进数据库集合中

        # 先将向量列表构造成新数据：向量 + 文本 + 来源
        data_list = [
            {
                "id":self.get_fingerprint(source,content),
                "vector":vector,
                "text":content,
                "source":source
            } for vector,content,source in zip(vector_list,content_list,source_list)
        ]
        # 将数据存入集合
        result = self.client.upsert(
            collection_name=self.collection_name,
            data=data_list
        )
        # logger.info(f"已存入{len(data_list)}条数据：\n{result}")
        logger.info(f"已存入{len(data_list)}条数据")

    # 对于失效source做清理（文档被整份删除之后，数据库对应source也应删除）
    # 前面只对失效chunk做清理
    # 传入target目录下所有文档内容（包括子目录），查询数据库所有source，对target目录下没有的做删除
    def detele_source(self,source_list):
        # 1.查询数据库所有source（可能很多，做翻页处理）
        iterator = self.client.query_iterator(
            collection_name=self.collection_name,
            filter="id>=0",
            output_fields=["source"]
        )
        all_db_source=[]
        while True:
            rows = iterator.next() # 默认每一页1000
            if not rows:
                break
            for row in rows:
                all_db_source.append(row["source"])
        # 关闭迭代器，防止内存泄漏
        iterator.close()
        # 对数据库存在但target目录不存在的文档做删除
        need_delete = set(all_db_source) - set(source_list)
        logger.info(f"11111111111111\n{need_delete}")
        logger.info(f"{set(all_db_source)}\n{set(source_list)}\n{need_delete}")
        if need_delete:
            self.client.delete(
                collection_name=self.collection_name,
                filter=f"source in {list(need_delete)}"
            )
            logger.info(f"已删除失效文档：{len(need_delete)}份")
        else:
            logger.info("目前没有失效文档")











    # 查询
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
































# # 基础版：全量更新（全部删除再新增）
#     def upsert_vector(self,vector_list,text_list,source):
#         # 将向量数据存进数据库集合中

#         # 先将向量列表构造成新数据：向量 + 文本 + 来源
#         data_list = [
#             {
#                 "id":i,
#                 "vector":vector,
#                 "text":text_list[i],
#                 "source":source
#             } for i,vector in enumerate(vector_list)
#         ]
#         # 将数据存入集合
#         result = self.client.upsert(
#             collection_name=self.collection_name,
#             data=data_list
#         )
#         logger.info(f"已存入{len(data_list)}条数据：\n{result}")