from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def load_embedding_model(model_name=MODEL_NAME):
    """加载 embedding 模型；缓存起来，避免每次调用都重新加载。"""

    return SentenceTransformer(model_name)


def embed_texts(texts, model_name=MODEL_NAME):
    """把一组文本转换成向量。"""

    model = load_embedding_model(model_name)

    # normalize_embeddings=True 会把向量归一化，方便做相似度检索
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings.tolist()
