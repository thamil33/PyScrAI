from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder


crossencorder_rerank_model= CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
textembed_model = SentenceTransformer("multi-qa-distilbert-cos-v1")



