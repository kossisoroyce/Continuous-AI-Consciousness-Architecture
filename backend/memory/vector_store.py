"""
Vector Store Memory using ChromaDB.
Handles semantic storage and retrieval of interactions.
"""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

class VectorStore:
    def __init__(self, persistence_dir: str = "./nurture_data/vector_store"):
        self.client = chromadb.PersistentClient(path=persistence_dir)
        
        # Use a local embedding model
        # 'all-MiniLM-L6-v2' is fast and efficient for CPU usage
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Collection for general interaction history
        self.interactions = self.client.get_or_create_collection(
            name="interactions",
            embedding_function=self.embedding_fn
        )
        
        # Collection for specific facts (could be separate or shared)
        self.facts = self.client.get_or_create_collection(
            name="facts",
            embedding_function=self.embedding_fn
        )
    
    def add_interaction(self, user_input: str, assistant_response: str, metadata: Dict[str, Any]):
        """Add an interaction pair to memory."""
        # We store the user input as the primary document for retrieval query matching
        # But we store the full exchange in metadata
        
        doc_id = f"int_{datetime.now().timestamp()}"
        
        # Clean metadata for Chroma (no nested dicts allowed usually)
        flat_metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "interaction",
            "assistant_response": assistant_response[:1000] # Truncate if too long
        }
        # Add basic metadata fields
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                flat_metadata[k] = v
        
        self.interactions.add(
            documents=[user_input],
            metadatas=[flat_metadata],
            ids=[doc_id]
        )
    
    def add_fact(self, fact_content: str, metadata: Dict[str, Any]):
        """Add a specific extracted fact to memory."""
        doc_id = f"fact_{datetime.now().timestamp()}"
        
        flat_metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "fact"
        }
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                flat_metadata[k] = v
                
        self.facts.add(
            documents=[fact_content],
            metadatas=[flat_metadata],
            ids=[doc_id]
        )

    def search_context(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant context (facts and past interactions).
        Returns a mixed list of results.
        """
        results = []
        
        # Query facts
        fact_results = self.facts.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Query past interactions
        int_results = self.interactions.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Process facts
        if fact_results['documents']:
            for i, doc in enumerate(fact_results['documents'][0]):
                results.append({
                    "content": doc,
                    "type": "fact",
                    "distance": fact_results['distances'][0][i] if 'distances' in fact_results else 0,
                    "metadata": fact_results['metadatas'][0][i]
                })
        
        # Process interactions
        if int_results['documents']:
            for i, doc in enumerate(int_results['documents'][0]):
                # Format: "User: [doc] \n Assistant: [response]"
                response = int_results['metadatas'][0][i].get('assistant_response', '')
                content = f"User: {doc}\nAssistant: {response}"
                
                results.append({
                    "content": content,
                    "type": "interaction",
                    "distance": int_results['distances'][0][i] if 'distances' in int_results else 0,
                    "metadata": int_results['metadatas'][0][i]
                })
        
        # Sort by relevance (distance)
        results.sort(key=lambda x: x['distance'])
        
        return results[:n_results]
