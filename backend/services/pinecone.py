import os 
from uuid import uuid4
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from backend.utils.embed import huggingface_emb
from pinecone import ServerlessSpec
from backend.utils.logger import log_message
import time


# logger = get_logger(__name__)


pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = os.getenv("index_name")
embeddings = huggingface_emb()




def create_vector_db(documents):
    """Initializes a Pinecone vector store with the specified index name and embedding.

    This function checks for the existence of the specified Pinecone index. If it does not exist,
    it creates a new one with the provided configuration. Then, it initializes a vector store 
    using the Pinecone index and a Hugging Face embedding model.

    Args:
        pc (Pinecone): An initialized Pinecone client.
        huggingface_emb: The embedding function or model compatible with LangChain.
        index_name (str, optional): Name of the Pinecone index to use or create.

    Returns:
        PineconeVectorStore: An initialized LangChain-compatible vector store.

    Raises:
        Exception: If there is an error during index creation or vector store initialization.
    """
    try:

        if not pc.has_index(index_name):
            # logger.info(f"Index '{index_name}' does not exist. Creating a new index.")
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",

                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            # logger.info(f"Index '{index_name}' created successfully.")
            
        # else:
            # logger.info(f"Index '{index_name}' already exists.")

        index = pc.Index(index_name)
        vector_store = PineconeVectorStore(index=index, embedding=embeddings)
        uuids = [str(uuid4()) for _ in range(len(documents))]

        # batch_size = 100
        # for i in range(0, len(documents), batch_size):
        #     batch = documents[i:i+batch_size]
        #     # ingest this batch
        #     vector_store.add_documents(documents=batch, ids=uuids)
        #     print(f"Ingested batch {i//batch_size + 1}")
        #     time.sleep(5)  # wait 1 second before next batch

        vector_store.add_documents(documents=documents, ids=uuids)
        # logger.info(f"Pinecone vector store initialized with index '{index_name}'.")

        return index_name

    except Exception as e:
        # logger.exception("An error occurred while initializing the Pinecone vector store.")
        raise




def retrieve_documents(vector_store, query):
#     retriever = vector_store.as_retriever(
#     search_type="similarity_score_threshold",
#     search_kwargs={"k": 10, "score_threshold": 0.4},
# )
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5,                  # fewer, more precise results
            "fetch_k": 20,            # retrieve more before reranking
            "score_threshold": 0.75,  # stricter threshold for semantic precision
        },
    )
    response = retriever.invoke(query)

    return response



def load_vectordb(index_name, embeddings):
       
       vectorstore_from_docs = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
       return vectorstore_from_docs




