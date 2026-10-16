"""  
文档加载模块

目前支持加载格式：
    .txt、.md、.pdf、.docx、.csv、.json
"""

# 加入项目根目录，单跑文件测试模块时使用，防止找不到其他路径的导入包
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))





import os
import shutil

from langchain_community.document_loaders import (CSVLoader, Docx2txtLoader,
                                                  JSONLoader, PyPDFLoader,
                                                  TextLoader)

from config.settings import Setting
from utils.logger import logger


# 进阶版：传入目录路径，支持多种格式文档加载，且能加载多份
class DocumentLoader:
    """  
    支持多种文档格式：.txt、.md、.pdf、.docx、.csv、.json

    支持多文件加载

    加载结束的文件会被移入其他文件夹中，加载失败的文件还在原处
    """
    # 获取目录路径（1.源文档存放处；2.加载完的文档存放处）
    def __init__(
            self,
            source_folder_path:str=Setting.KNOWLEDGE_SOURCE_FOLDER_PATH,
            target_folder_path:str=Setting.KNOWLEDGE_TARGET_FOLDER_PATH
    ):
        # 将字符串路径转成Path对象，使用其中的mkdir方法：不存在路径就创建
        # parents=True表示可以创建多级目录
        # exist_ok=True表示存在路径就跳过
        try:
            self.source_path = Path(source_folder_path)
            self.target_path = Path(target_folder_path)
            if not self.source_path.exists():
                raise FileNotFoundError(f"源路径不存在：{self.source_path}")
            self.target_path.mkdir(parents=True,exist_ok=True)
            logger.info("文档加载器初始化完成")
        except Exception as e:
            logger.error(f"文档加载器初始化失败：{e}")
            raise

    # 对单独一份文档进行加载（先判断文档格式）
    def load_single_file(self,file_path):
        # 判断文档格式
        # 先将字符串路径转成Path对象，后续调用里面的suffix方法
        path = Path(file_path)
        # 获取文件后缀（suffix取最后一个后缀；suffixes取所有后缀）
        suffix = path.suffix.lower()
        # 加载
        if suffix in [".txt",".md"]:
            loader = TextLoader(file_path,encoding="utf-8")
        elif suffix == ".pdf":
            loader = PyPDFLoader(file_path)
        elif suffix == ".docx":
            loader = Docx2txtLoader(file_path)
        elif suffix == ".csv":
            loader = CSVLoader(file_path,encoding="utf-8-sig")
        elif suffix == ".json":
            loader = JSONLoader(
                file_path,
                jq_schema=".", # 加载全部内容
                text_content=False # 允许里面的内容不是字符串，而是对象/字典等格式
            )
        else:
            raise ValueError(f"不支持文档格式：{file_path}")
        
        document_list = loader.load()
        # 记录来源，用于后续答案溯源
        for doc in document_list:
            # 来源只存子目录下完整路径，方便后续删除库中整份来源数据chunks时和目标路径下所有子目录路径做对比
            # 如果存完整路径，数据库里是source+子目录路径，但判断的是target+子目录路径
            source = Path(file_path).relative_to(Setting.KNOWLEDGE_SOURCE_FOLDER_PATH)
            doc.metadata["source"] = str(source)
            doc.metadata["type"] = suffix
        return document_list

    # 多文档加载
    def load_all_files(self):
        all_files = [] # 是一个大的document对象列表，存放所有文档加载之后的document对象
        # 获取所有文档路径
        all_file_path = self.get_all_file(self.source_path)
        # 加载每一份文档
        errors = [] # 加载失败的文档路径+失败原因
        i = 0 # 加载成功的文档数量
        for file_path in all_file_path:
            try:
                document_list = self.load_single_file(file_path)
                # 不能用append，因为要加的不是一个列表，而是列表里的每一个document对象
                all_files.extend(document_list)
                i += 1
                logger.info(f"文档{file_path}加载完成，共{len(document_list)}个片段") # 部分文档加载完可能不止一个片段
            except Exception as e:
                logger.error(f"文档{file_path}加载失败：\n{e}")
                errors.append((file_path,e))      
        # 记录加载完的所有文档
        logger.info(f"所有文档加载完成，共{len(all_file_path)}份\n加载成功{i}份，共{len(all_files)}个片段\n加载失败{len(errors)}份：\n{errors}")
        return all_files

    # 获取路径下所有文档（这里加载文档要用source，后面删除失效source需要用target）
    def get_all_file(self,folder_path):
        all_file_path = []
        for p in Path(folder_path).rglob("*"):
            if p.is_file():
                all_file_path.append(str(p))
        return all_file_path





# 单跑文件测试模块
if __name__ == "__main__":
    loader = DocumentLoader()
    # docs = loader.load()
    docs = loader.load_all_files()
    print(f"docs:\n{docs}")












































# # 多文档加载
#     def load_all_files(self):
#         all_files = [] # 是一个大的document对象列表，存放所有文档加载之后的document对象
#         # 递归遍历每一层：root是当前目录名；_是当前目录下所有子目录名列表；files是当前目录下所有文档名列表
#         # Path().walk()适用于python3.12及以上；可替换：os.walk(source_path)
#         for root,_,files in self.source_path.walk():
#             # 对每一份文档进行加载
#             for file in files:
#                 # 拼接文档路径：当前目录名 + 文档名
#                 file_path = root / file
#                 try:
#                     # root已经是Path对象，file是字符串，拼接的file_path也是Path对象，所以转成字符串str()
#                     document_list = self.load_single_file(str(file_path))
#                     # 不能用append，因为要加的不是一个列表，而是列表里的每一个document对象
#                     all_files.extend(document_list)
#                     logger.info(f"文档{str(file_path)}加载完成，共{len(document_list)}个片段")
#                     # 把加载成功的文档移走（保留子目录格式不变）
#                     # relative是相对路径（子目录+文件名）：文件总路径-源路径
#                     relative = file_path.relative_to(self.source_path)
#                     # relative.parent获取子目录，与目标路径进行拼接
#                     shutil.move(file_path, self.target_path / relative.parent)
#                 except Exception as e:
#                     logger.error(f"文档{file_path}加载失败：\n{e}")
#                     # 加载失败的文档不进行移动
        
#         # 记录加载完的所有文档
#         logger.info(f"所有文档加载完成，共{len(all_files)}个片段")
#         return all_files








                    





# # 基础版：传入文档路径，仅支持加载.txt格式的文档，且仅能加载一份
# class DocumentLoader:
#     """  
#     将知识库文件加载为document列表

#     目前支持加载方式：
#         TextLoader()
#     """
#     # 获取文件路径
#     def __init__(self,file_path:str=Setting.KNOWLEDGE_FILE_PATH):
#         self.file_path = file_path

#     # 加载文件
#     def load(self)->list:
#         # 先判断文件是否存在
#         if not Path(self.file_path).exists(): # Path对象方式
#         # if not os.path.exists(self.file_path): # os方式
#             logger.error(f"知识库文件{self.file_path}不存在")
#             raise FileNotFoundError(
#                 f"知识库文件【{self.file_path}】不存在\n"
#                 "请确认文件是否放入data/目录下，"
#                 "或者文件路径是否配置正确"
#             )
#         loader = TextLoader(
#             file_path=self.file_path,
#             encoding="utf-8"
#         )
#         document_list = loader.load()
#         # 记录来源，后续会新增功能“答案溯源”
#         # 部分文档加载器不会自带source字段
#         for doc in document_list:
#             if "source" not in doc.metadata:
#                 doc.metadata["source"] = self.file_path

#         logger.info(f"知识库文档{self.file_path}已加载完成")

#         return document_list

