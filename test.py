# 猴子补丁，替换swagger的cdn为国内可访问的镜像
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import applications
def swagger_patch(*args, **kwargs):
    return get_swagger_ui_html(
        *args,
        **kwargs,
        swagger_js_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui.css",
    )
applications.get_swagger_ui_html = swagger_patch







from fastapi import FastAPI,Path,Query
import uvicorn
from typing import Annotated

app = FastAPI()





@app.get("/")
def root_user():
    return "你好，公子"

@app.get("/say_hello/{name}")
def hello_user(
    name : Annotated[
        str,
        Path(...,min_length=2,max_length=3,description="姓名")
    ]
):
    name += " haha~"
    return f"你好，{name}"

@app.get("/news/{id}")
def news_id(
    id : Annotated[
        int,
        Path(...,ge=1,le=100,description="新闻ID")
    ]
):
    return f"新闻ID：{id}"

@app.get("/news/name/{name}")
def news_name(
    name : Annotated[
        str,
        Path(...,min_length=2,max_length=10,description="新闻名称")
    ]
):
    return f"新闻名称：{name}"

@app.get("/user/{id}")
def user(
    id : Annotated[
        int,
        Path(...,description="用户ID")
    ],
    name : str = Query(default="公子",description="用户名称")
):
    return f"用户ID：{id}，用户名称：{name}"

@app.get("/book")
def book_info(
    price : Annotated[
            int,
            Query(description="价格",ge=50,le=100)
        ],
    name : str = Query("Python开发",description="图书分类",min_length=5,max_length=255),
    # name : Annotated[
    #     str,
    #     Query(description="图书分类",min_length=5,max_length=255)
    # ] = "Python开发",
):
    return f"图书分类：{name}，价格：{price}"

# 新增图书：书名、作者、出版社、价格
from pydantic import BaseModel,Field
class BookInfo(BaseModel):
    name : Annotated[str,Field(description="书名",min_length=2,max_length=3)]
    writer : Annotated[str,Field(description="作者")] = "公子"
    source : Annotated[str,Field(description="出版社")]
    price : Annotated[int,Field(description="价格")]

@app.post("/book/add_book")
def add_book(book_info : BookInfo):
    # return f"新增书籍的信息：\n{book_info}"
    return book_info

from fastapi.responses import HTMLResponse,FileResponse
@app.get("/html_test",response_class=HTMLResponse)
def html_hello():
    # return "<h1>这是一级标题</h1>"
    return "hello"

# @app.get("/file",response_class=FileResponse)
# def file_txt():
#     file_path = "D:/AboutPython/Project/Study/总结/test_img.webp"
#     return file_path

@app.get("/file")
def file_txt():
    file_path = "D:/AboutPython/Project/Study/总结/test_img.webp"
    return FileResponse(file_path)





if __name__ == "__main__":
    uvicorn.run("test:app",host="localhost",port=8000,reload=True)









































# """  
# app_for_fast_api.py
# """
# # 猴子补丁，替换swagger的cdn为国内可访问的镜像
# from fastapi.openapi.docs import get_swagger_ui_html
# from fastapi import applications
# def swagger_patch(*args, **kwargs):
#     return get_swagger_ui_html(
#         *args,
#         **kwargs,
#         swagger_js_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui-bundle.js",
#         swagger_css_url="https://cdn.staticfile.org/swagger-ui/5.9.0/swagger-ui.css",
#     )
# applications.get_swagger_ui_html = swagger_patch



# from fastapi import FastAPI
# import uvicorn
# from pydantic import BaseModel,Field
# from typing import Annotated
# from core.pipeline import RAGPipeline
# from utils.logger import logger
# app = FastAPI()

# try:
#     rag = RAGPipeline()
# except Exception as e:
#     logger.error(f"RAG初始化失败:\n{e}")
#     raise

# class Query(BaseModel):
#     question : Annotated[str,Field(description="用户输入的问题")]
# @app.post("/chat")
# def chat(query : Query):
#     answer = rag.ask(query.question)
#     return {"answer":answer}



# if __name__ == "__main__":
#     uvicorn.run("app_for_fast_api:app",host="0.0.0.0",port=8000)



