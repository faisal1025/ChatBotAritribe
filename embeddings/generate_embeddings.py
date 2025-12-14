from dotenv import load_dotenv
import os
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_chunks(file_path, chunk_size=1000, chunk_overlap=200):    
    try:
        with open(file=file_path, mode='r', encoding='utf-8') as file:
            content = file.read()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            separators=["\n\n", "\n", " ", ""],
            chunk_overlap=chunk_overlap,
            length_function=len
        )

        chunks = text_splitter.split_text(content)
        return chunks
    except FileNotFoundError:
        print(f"Error: file {file_path} not found")
        return []
    except Exception as e:
        print(f"Error: reading file {e}")
        return []
    
def create_chunks_from_files(file_paths, chunk_size=1000, chunk_overlap=200):
    all_chunks = []
    for file_path in file_paths:
        chunks = create_chunks(file_path, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)
    print(f"Created a total of {len(all_chunks)} chunks from {len(file_paths)} files")
    return all_chunks

def create_embeddings(chunks):
    if not chunks:
        print("No chunks created, skipping embeddings")
        return []
    try:

        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunks,
            encoding_format="float"
        )

        vectors = [item.embedding for item in embedding_response.data]
        print(f"Got, {len(vectors)} embeddings, each of length {len(vectors[0])}")

        return vectors
    except Exception as e:
        print(f"Error: unable to create embeddings {e}")
        return []
    
def create_embeddings_per_file(file_paths, chunk_size=1000, chunk_overlap=200):
    """Process each file separately with metadata tracking"""
    all_embeddings = []
    all_chunks = []
    all_metadata = []
    
    for file_path in file_paths:
        print(f"Processing file: {file_path}")
        
        # Create chunks for this file
        chunks = create_chunks(file_path, chunk_size, chunk_overlap)
        
        if not chunks:
            print(f"No chunks created for {file_path}, skipping...")
            continue
        
        # Create embeddings for this file's chunks
        try:
            embedding_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=chunks,
                encoding_format="float"
            )
            
            vectors = [item.embedding for item in embedding_response.data]
            
            # Create metadata for each chunk
            metadata = [
                {
                    "source_file": file_path,
                    "filename": os.path.basename(file_path),
                    "chunk_index": i,
                    "total_chunks_in_file": len(chunks)
                }
                for i in range(len(chunks))
            ]
            
            # Collect results
            all_embeddings.extend(vectors)
            all_chunks.extend(chunks)
            all_metadata.extend(metadata)
            
            print(f"✅ Created {len(vectors)} embeddings for {file_path}")
            
        except Exception as e:
            print(f"❌ Error creating embeddings for {file_path}: {e}")
    
    print(f"Total: {len(all_embeddings)} embeddings from {len(file_paths)} files")
    return all_embeddings, all_chunks, all_metadata