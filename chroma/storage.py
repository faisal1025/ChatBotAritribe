import os
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")

def semantic_search(user_prompt, collection_name="documents", n_results=3):
    """Perform semantic search based on user query"""
    try:
        # Step 1: Convert user query to embedding
        query_embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=user_prompt,
            encoding_format="float"
        )
        
        # Step 2: Extract embedding vector
        query_embedding = query_embedding_response.data[0].embedding
        
        # Step 3: Search similar chunks in ChromaDB
        results = query_context(
            query_embedding=query_embedding,
            collection_name=collection_name,
            n_results=n_results
        )
        
        # Step 4: Format and return results
        if results and results['documents']:
            print(f"Found {len(results['documents'][0])} relevant chunks:")
            print("-" * 50)
            
            docs = []
            source = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"Result {i+1}:")
                print(f"Source: {metadata.get('filename', 'Unknown')}")
                print(f"Content: {doc[:100]}...")  # First 200 characters
                print("-" * 50)
                docs.append(doc)
                source.append(metadata.get('filename', 'Unknown'))

            return docs, source
        else:
            print("No relevant results found.")
            return []
            
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []


def save_context(embeddings, chunks, metadata, collection_name="documents"):
    collection = chroma_client.get_or_create_collection(name=collection_name)


    ids = [f"{meta.get('filename', 'unknown')}_{i}" for meta, i in zip(metadata, range(len(metadata)))]

    collection.add(
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadata,
        ids=ids
    )

    return True

def query_context(query_embedding, collection_name="documents", n_results=3):
    """Query similar documents from ChromaDB"""
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        
    )
    
    return results