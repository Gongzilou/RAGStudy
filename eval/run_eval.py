"""  
RAG评估脚本

检索质量 + 生成质量
检索质量代表文档召回率，质量高表示检索没问题
生成质量代表模型有没有答到点上，质量高表示生成没问题

根据检索命中率（检索到哪些文档） + 关键词覆盖，
对比自己写的测试集test_cases.json,
生成评估报告

后续完成功能升级：混合检索 + 重排，再进行一次评估，
进行升级前后的对比
"""

import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).parent.parent
    )
)





import json

from core.agent import Agent
from core.embedding import Embedding
from core.reranker import Reranker
from core.vector_store import MilvusStore
from utils.logger import logger


# 加载测试集test_cases.json
def load_test_cases(path="eval/test_cases.json"):
    with open(path,encoding="utf-8") as f:
        return json.load(f)

# 评估所有问题
def evaluate(cases,embed,vector_store,agent,reranker):
    # 对于每个问题，如果期望来源里有被召回的，就属于命中，命中次数+1
    hit_count = 0
    # 记录每个问题的检测情况
    all_query_result = []
    for case in cases:
        query = case["query"]
        logger.info(f"[{case["id"]}/{len(cases)}]评估：{query}")

        # 1.问题嵌入 + 检索召回，不要返回上下文，只要原始结果，提取source
        
        # # 初始化嵌入模型
        # embed = Embedding()
        # 问题转向量
        query_vector = embed.embed_query(query)
        # # 初始化数据库
        # vector_store = MilvusStore()
        # 检索召回
        recall_result = vector_store.search(query,query_vector)

        # rerank重排
        result = reranker.rerank(query,recall_result,3)




        if case["id"] == 19:
            logger.info(f"测试记录第{case["id"]}个问题的召回内容")
            for row in result:
                logger.info(f"片段{row["id"]}:\n{row["entity"].get("text","unknow")}")







        # 提取召回的source
        result_source = {row["entity"].get("source","unknow") for row in result}
        # 判断期望来源里是否有被召回的
        # 只要命中，返回true，后面不再遍历
        hit = any(source in result_source for source in case["expected_sources"])
        hit_count += int(hit)

        # 2.根据问题进行回答，判断是否有关键词被命中
        # 将召回结果进行上下文拼接
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
        # # 初始化Agent
        # agent = Agent()
        # 上下文 + 问题 同时给模型进行回答
        # answer = agent.answer(query,context)
        answer = "".join(agent.answer(query,context))
        # 提取命中的关键词
        keywords = [kw for kw in case["expected_keywords"] if kw in answer]
        # 记录该问题的检测情况
        all_query_result.append(
            {
                # ID
                "id" : case["id"],
                # 问题
                "query" : query,
                # 是否命中期望来源
                "hit" : hit,
                # 所有召回来源
                "recalled_sources" : sorted(result_source),
                # 期望来源
                "expected_sources" : case["expected_sources"],
                # 回答
                "answer" : answer,
                # 回答中命中的关键词
                "covered" : keywords,
                # 回答中没有命中的关键词
                "missed" : [kw for kw in case["expected_keywords"] if kw not in answer],
            }
        )

    return {
        "total" : len(cases),
        "recall_hit_rate" : round(hit_count / len(cases), 3),   # 检索命中率
        "results" : all_query_result,
    }





if __name__ == "__main__":
    # 加载测试集
    cases = load_test_cases()
    # 初始化嵌入模型
    embed = Embedding()
    # 初始化数据库
    vector_store = MilvusStore()
    # 初始化Agent
    agent = Agent()
    # 初始重排序器
    reranker = Reranker()
    # 根据测试集进行评估,生成评估报告
    report = evaluate(cases,embed,vector_store,agent,reranker)

    print("="*30)
    print(f"测试用例：{report['total']}条")
    print(f"检索命中率：{report['recall_hit_rate']}")
    print("="*30)

    # 存报告（加时间戳，不覆盖历史报告）
    from datetime import datetime

    # 存放路径
    path = Path("eval/reports")
    # 创建路径，可以是多级目录，存在就跳过
    path.mkdir(parents=True,exist_ok=True)
    # 文档名加时间戳
    file_name = path / f"report_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        # ensure_ascii=False表示中文等非ASCII字符保留原样
        # indent=2表示每层缩进2格，美化输出
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"报告已保存：{file_name}")





