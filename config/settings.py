"""  
全局配置模块，真实配置在.env文件中
"""

# 加入项目根目录，单跑文件测试模块时使用
import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





# 加载环境变量
import os

from dotenv import load_dotenv

load_dotenv()

class Setting:
    # 知识库文件的存储路径
    KNOWLEDGE_FILE_PATH = os.getenv("KNOWLEDGE_FILE_PATH")

    # log日志的存储路径
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
    # log等级
    LOG_LEVEL = os.getenv("LOG_LEVEL")

    # 文档切块大小
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
    # 每块重叠大小
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP"))

    # 硅基流动平台
    # 嵌入模型名称(使用模型为：BAAI/bge-m3)
    EMBED_MODEL = os.getenv("EMBED_MODEL")
    # 嵌入模型密钥
    EMBED_API_KEY = os.getenv("EMBED_API_KEY")
    # 嵌入模型地址
    EMBED_BASE_URL = os.getenv("EMBED_BASE_URL")
    # 嵌入模型维度（向量数据库创建集合时需要）
    EMBED_DIMENSION = int(os.getenv("EMBED_DIMENSION"))

    # Milvus服务端地址
    MILVUS_URL = os.getenv("MILVUS_URL")
    # Milvus数据库名称
    MILVUS_DB_NAME = os.getenv("MILVUS_DB_NAME")
    # Milvus集合名称
    MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION")
    # 检索返回的结果数量
    RETRIEVER_TOP_K = int(os.getenv("RETRIEVER_TOP_K"))





if __name__ == "__main__":
    setting = Setting()
    print(f"KNOWLEDGE_FILE_PATH:\n{setting.KNOWLEDGE_FILE_PATH}")