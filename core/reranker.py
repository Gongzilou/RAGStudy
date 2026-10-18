"""  
重排序模块

针对两路召回的去重结果进行重排序
使用模型为: BAAI/bge-reranker-v2-m3
"""

import requests

from config.settings import Setting
from utils.logger import logger


class Reranker:

    def __init__(self):
        # 初始化，获取地址、密钥、重排序模型名称
        # 使用模型为：BAAI/bge-reranker-v2-m3
        self.model = Setting.RERANK_MODEL
        self.api_key = Setting.EMBED_API_KEY
        # 地址会多上后面一部分"/rerank"
        self.base_url = Setting.EMBED_BASE_URL + "/rerank"
        logger.info("重排序器初始化成功")

    def rerank(self,query,recall_result,limit):
        # 将用户提问 与 去重后的召回结果 一一对应进行打分，返回分数最高的几条结果
        
        # 没有召回结果不需要排序
        if not recall_result:
            return []

        # 提取召回结果的所有内容
        text_list = [chunk["entity"].get("text","unknow") for chunk in recall_result]

        # 向硅基流动服务器发送请求，请求进行重排序
        # 1.请求头
        headers = {
            "Authorization":f"Bearer {self.api_key}",
            # 告诉服务器，请求体里的是json格式数据，按json解析
            "Content-Type":"application/json"
        }
        # 2.请求体
        payload = {
            "model":self.model,
            "query":query,
            "documents":text_list,
            "top_n":limit
        }
        # 3.发送请求
        try:
            response = requests.post(
                url=self.base_url,
                json=payload,
                headers=headers
            )
            logger.info("重排序请求发送成功")
        except Exception as e:
            logger.error(f"重排序请求发送失败：{e}")
            raise
        # 4.获取结果（已经排完序的结果，得分高的在前面）
        # 服务器返回的也是json格式的数据
        result = response.json()

        # 获取的结果类似这样：
        # index是该chunk在text_list对应的下标
        # relevance_score表示该chunk的得分
        # {
        #     "results": [
        #         {"index": 0, "relevance_score": 0.98},   // 第0个文档最相关
        #         {"index": 2, "relevance_score": 0.12},   // 第2个其次
        #         {"index": 1, "relevance_score": 0.05}    // 第1个最不相关
        #     ]
        # }

        # 最后，根据index下标返回recall_result中对应的那些chunk
        rerank_list = []
        for row in result["results"]:
            index = row["index"]
            rerank_list.append(recall_result[index])

        logger.info("已对检索结果进行重排序")
        return rerank_list
        


