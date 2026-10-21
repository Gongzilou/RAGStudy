"""  
fastapi接口模块

连接前端与后端
"""
# 不添加这部分，输入url加载不出来
# 猴子补丁，替换swagger的cdn为国内可访问的镜像
from fastapi import applications
from fastapi.openapi.docs import get_swagger_ui_html
def swagger_patch(*args, **kwargs):
    return get_swagger_ui_html(
        *args,
        **kwargs,
        swagger_js_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui.css",
    )
applications.get_swagger_ui_html = swagger_patch





from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field

from core.pipeline import RAGPipeline
from utils.logger import logger

# 初始化RAG
try:
    rag = RAGPipeline()
except Exception as e:
    logger.error(f"RAG初始化失败:\n{e}")
    raise

# 实例化FastAPI
app = FastAPI()

# 定义请求体参数
class Query(BaseModel):
    question : Annotated[str,Field(description="用户的提问")]
# 使用【路由】连接【url】和【函数】
@app.post("/chat")
def chat(query : Query):
    answer = rag.ask(query.question)
    return {"answer":answer}





if __name__ == "__main__":
    import uvicorn

    # uvicorn.run("rag_app:app",host="0.0.0.0",port=8000)
    uvicorn.run(app,host="0.0.0.0",port=8000)