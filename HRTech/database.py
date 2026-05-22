import chromadb
import uuid
from chromadb.utils import embedding_functions

# Türkçe destekli çok dilli gömme (embedding) modelini tanımlıyoruz
turkce_model = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

# Yerel vektör veritabanını başlat
chroma_client = chromadb.PersistentClient(path="./hr_vector_db")

# Koleksiyonu oluştururken Türkçe modelimizi içine entegre ediyoruz
collection = chroma_client.get_or_create_collection(
    name="cv_candidates", 
    embedding_function=turkce_model
)

def add_candidate(isim, ozellikler_metni, dosya_yolu, raw_json):
    """Adayı vektör veritabanına ekler."""
    doc_id = str(uuid.uuid4())
    collection.add(
        documents=[ozellikler_metni],
        metadatas=[{
            "isim": isim,
            "orijinal_dosya": dosya_yolu,
            "raw_json": raw_json
        }],
        ids=[doc_id]
    )
    return doc_id

def search_candidates(job_description, top_k=3):
    """İlan açıklamasına göre vektörel arama yapar."""
    results = collection.query(
        query_texts=[job_description],
        n_results=top_k
    )
    return results