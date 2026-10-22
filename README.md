# RAGStudy

一个基于 LangChain 和 Milvus 的产品知识库问答项目。项目从本地文档构建向量知识库，通过语义检索与 BM25 关键词检索召回内容，再使用重排模型筛选相关片段，最后由本地聊天模型根据检索上下文生成回答。

## 功能概览

- 批量加载 `.txt`、`.md`、`.pdf`、`.docx`、`.csv` 和 `.json` 文档。
- 使用 `RecursiveCharacterTextSplitter` 切分文档，并通过嵌入模型生成向量。
- 使用 Milvus 存储文档，并执行向量检索和 BM25 关键词检索。
- 对两路召回结果去重后调用重排模型，再将相关片段交给聊天模型。
- 支持命令行流式问答、FastAPI 流式接口和静态网页前端。
- 提供问答评估脚本、测试用例及 JSON 评估报告。

## 项目结构

```text
.
├── config/
│   └── settings.py        # 从 .env 读取项目配置
├── core/
│   ├── agent.py           # 聊天模型与流式回答
│   ├── document_loader.py # 多格式文档加载
│   ├── embedding.py       # 文本和问题嵌入
│   ├── pipeline.py        # 文档同步及 RAG 流程编排
│   ├── reranker.py        # 召回结果重排
│   ├── retriever.py       # 检索与上下文组装
│   ├── text_splitter.py   # 文档切分
│   └── vector_store.py    # Milvus 集合、索引、读写和检索
├── data/
│   ├── source/            # 待导入文档
│   └── target/            # 成功导入后归档的文档
├── eval/
│   ├── test_cases.json    # 评估问题与预期结果
│   ├── run_eval.py        # 运行评估
│   └── reports/           # 评估报告
├── RAG_HTML/              # 静态网页前端（由Agent开发而成）
├── logs/                  # 按日期生成的运行日志
├── main.py                # 命令行问答入口
├── rag_app.py             # FastAPI 与静态网页入口
└── requirements.txt       # 当前 Conda 环境的 pip freeze 快照
```

## 环境要求

当前项目环境及已核对的服务版本：

- Python **3.13.12**
- Milvus Server **2.5.27**；项目使用 Milvus BM25 Function 自动从文本字段生成稀疏向量，需使用 **Milvus 2.5.0 或更高版本**。
- PyMilvus **2.6.12**（Python 客户端版本，与 Milvus Server 版本是不同概念）。
- Ollama，且本地已安装项目配置的聊天模型 `qwen2.5:14b-instruct-q4_K_M`。
- Ollama 的 LangChain 适配由当前环境中的 `langchain-community` 提供；当前依赖快照不需要额外安装 `langchain-ollama`。
- SiliconFlow 兼容 API：项目用它调用嵌入模型和重排模型。

`requirements.txt` 是 `langchain-study` Conda 环境的完整 `pip freeze` 快照（包含开发环境中的包，不只是应用的直接依赖）。可在 Python 3.13 环境中安装：

```powershell
conda create -n ragstudy python=3.13.12
conda activate ragstudy
python -m pip install -r requirements.txt
```

Milvus 和 Ollama 是独立服务，不会由 `pip install` 安装。请分别启动 Milvus 2.5.0+ 和 Ollama，并确保它们可从项目配置的地址访问。Ollama 默认服务地址通常是 `http://127.0.0.1:11434`；可用 `ollama list` 检查模型是否已经安装，需要时运行：

```powershell
ollama pull qwen2.5:14b-instruct-q4_K_M
```

## 配置

在项目根目录创建 `.env`。以下是配置示例；请替换 API 密钥，不要将真实密钥提交到版本库：

```dotenv
KNOWLEDGE_SOURCE_FOLDER_PATH=./data/source
KNOWLEDGE_TARGET_FOLDER_PATH=./data/target

LOG_FILE_PATH=./logs
LOG_LEVEL=INFO

CHUNK_SIZE=200
CHUNK_OVERLAP=40

EMBED_MODEL=BAAI/bge-m3
EMBED_MODEL_PROVIDER=openai
EMBED_API_KEY=替换为你的API密钥
EMBED_BASE_URL=https://api.siliconflow.cn/v1
EMBED_DIMENSION=1024
RERANK_MODEL=BAAI/bge-reranker-v2-m3

MILVUS_URL=http://127.0.0.1:19530
MILVUS_DB_NAME=RAG_Milvus_DB
MILVUS_COLLECTION=RAG_Milvus_COLL
RETRIEVER_TOP_K=5

CHAT_MODEL=qwen2.5:14b-instruct-q4_K_M
CHAT_MODEL_PROVIDER=ollama
```

`EMBED_API_KEY` 用于嵌入服务。重排服务使用 `EMBED_BASE_URL` 拼接 `/rerank`。注意：目前 [`core/reranker.py`](./core/reranker.py) 中的 Authorization 请求头仍是占位值；在使用重排功能前，需要在该模块中配置服务要求的认证头，否则远程重排请求可能认证失败。

`EMBED_DIMENSION` 必须与嵌入模型实际输出维度及 Milvus 集合 schema 一致。更改维度不会自动修改已存在集合的 schema；已有集合需要按实际数据迁移/重建并重新入库。

## 添加或更新知识库

1. 将支持格式的文档放入 `data/source/`，子目录也会递归扫描。
2. 启动命令行或 API 服务时，`RAGPipeline` 会加载源目录文档、切分并同步到 Milvus。
3. 含有新增 chunk 的文档在嵌入并写入 Milvus 后，会从 `data/source/` 移动到 `data/target/` 归档；加载失败的文档会留在源目录，并将错误写入日志。
4. 启动时会比较文档 chunk 指纹，尝试更新已变化的片段，并清理数据库中失效的来源。

因此，**新文档和需要重新导入的文档应放在 `data/source/`**。`data/target/` 是成功导入文档的归档目录，不是新文档的扫描入口。服务启动时会执行知识库同步，需确保 Milvus、嵌入服务以及重排服务配置可用。

切分长度和重叠大小分别由 `CHUNK_SIZE`、`CHUNK_OVERLAP` 控制。修改切分配置后，若要重建已归档文档的 chunks，需要将相应文档重新放入源目录并触发同步。

当前同步流程不是事务性的：会先删除数据库中不再匹配的旧 chunk，再处理新增 chunk。如果后续嵌入或写库失败，知识库可能处于部分更新状态；更新文档前应确认依赖服务可用，并保留原始文档备份。另外，只有检测到新增 chunk 时才执行文件归档；对已存在的完全相同文档重复放入源目录，不保证会再次归档。

## 启动问答

在项目根目录并激活配置好的 Python 环境后，选择一种入口启动。

### 命令行

```powershell
python main.py
```

在提示符中输入问题开始问答，输入 `exit` 退出。回答以流式文本形式输出。

### Web 前端和 API

```powershell
python rag_app.py
```

服务默认监听 `0.0.0.0:8000`。启动后访问 <http://127.0.0.1:8000/> 使用网页；Swagger 文档位于 <http://127.0.0.1:8000/docs>。该服务会在应用导入时初始化 RAG 流程，因此启动前需要确保配置和依赖服务可用。

聊天接口：

- `POST /chat`
- 请求体：`{"question": "你的问题"}`
- 成功响应：`text/plain` 流式文本，不是 JSON 对象。

网页默认请求 `http://127.0.0.1:8000/chat`。如果单独通过 Live Server 等方式托管 `RAG_HTML/`，页面与 API 不同源时需要配置后端 CORS 或使用同源反向代理。更多前端说明见 [`RAG_HTML/README.md`](./RAG_HTML/README.md)。

当前 API 未配置认证，并默认监听所有网络接口（`0.0.0.0`）；请仅在可信网络中运行，不要直接暴露到公网。每次请求只发送当前问题，不包含或保存前端聊天历史。

## 运行评估

确保 Milvus、嵌入、重排和聊天模型服务可用，然后从项目根目录运行：

```powershell
python eval/run_eval.py
```

脚本读取 [`eval/test_cases.json`](./eval/test_cases.json)，为每个问题执行检索、重排和回答，并将带时间戳的 JSON 报告写入 `eval/reports/`。当前报告包含期望来源命中率、实际召回来源、回答文本及预期关键词覆盖情况。关键词覆盖使用字符串包含判断，不等同于语义正确性；评估结果适合作为回归参考，不能单独代表答案质量。评估会实际调用模型服务，耗时和 API 用量会随测试用例数量增加。

## 日志

日志写入 `LOG_FILE_PATH` 指定目录，并按日期生成文件，例如 `logs/20261022.log`。运行级别由 `LOG_LEVEL` 控制。当前 `.gitignore` 已忽略 `.env`、日志和 Python 缓存。