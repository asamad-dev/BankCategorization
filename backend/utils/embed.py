from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def huggingface_emb():
    emb_model = os.getenv("emb_model")
    embed_fn = HuggingFaceEmbeddings(model_name=emb_model)
    return embed_fn