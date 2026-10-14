from pymilvus import MilvusClient
client = MilvusClient("http://127.0.0.1:19530")
client.use_database(db_name="RAG_Milvus_DB")
client.drop_collection("RAG_Milvus_COLL")
print(client.list_databases())
print(client.list_collections())
# client.drop_database(db_name="my_rag_db_2")
# 
# 