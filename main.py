"""  
主程序入口
"""

from core.pipeline import RAGPipeline
from utils.logger import logger


def main():

    # RAG初始化：加载、切分、嵌入等前期流程
    try:
        rag = RAGPipeline()
    except Exception as e:
        logger.error(f"RAG初始化失败:\n{e}")
        sys.exit(1) # exit(0)表示正常结束

    print("\n" + "="*30)
    print("RAG问答已就绪(输入exit退出)")
    print("="*30)
    while True:
        query = input("\n请输入问题:\n").strip()
        # 用户退出
        if query.lower() == "exit":
            print("再见！")
            break
        # 用户换行
        if not query:
            continue
        # 正常回答
        answer = rag.ask(query)
        print(f"AI:\n{answer}")





if __name__ == "__main__":
    main()
