"""
Memory Service - Continuity Brain using ChromaDB for local RAG

This service provides vector-based memory for projects, allowing agents
to recall details from previous chapters without loading the entire novel
into the context window.

Uses ChromaDB with the default local embedding function (all-MiniLM-L6-v2)
to avoid external API costs for embeddings.
"""

import os
import re
import hashlib
from typing import List, Optional, Dict, Any
from utils.logger import logger

# ChromaDB imports with graceful fallback
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. Memory service will be disabled.")


class ProjectMemory:
    """
    Manages vector-based memory for a project using ChromaDB.

    Each project gets its own isolated collection for storing and
    retrieving document chunks.
    """

    def __init__(self, persistence_path: str = "./chroma_db"):
        """
        Initialize the ProjectMemory service.

        Args:
            persistence_path: Directory path for ChromaDB persistence.
                            Defaults to ./chroma_db in the current working directory.
        """
        self.persistence_path = persistence_path
        self._client = None
        self._initialized = False

        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available. Memory features disabled.")
            return

        try:
            # Ensure persistence directory exists
            os.makedirs(persistence_path, exist_ok=True)

            # Initialize ChromaDB with persistence
            self._client = chromadb.PersistentClient(
                path=persistence_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self._initialized = True
            logger.info(f"ProjectMemory initialized with persistence at {persistence_path}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            self._initialized = False

    def is_available(self) -> bool:
        """Check if the memory service is available and initialized."""
        return self._initialized and self._client is not None

    def _get_collection_name(self, project_id: str) -> str:
        """
        Generate a safe collection name for a project.

        ChromaDB collection names must be 3-63 characters, start/end with
        alphanumeric, and contain only alphanumerics, underscores, or hyphens.
        """
        # Create a safe name by hashing if needed
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_id)

        # Ensure it starts with alphanumeric
        if not safe_name[0].isalnum():
            safe_name = 'p' + safe_name

        # Truncate if too long
        if len(safe_name) > 63:
            # Use hash to keep it unique but short
            hash_suffix = hashlib.md5(project_id.encode()).hexdigest()[:8]
            safe_name = safe_name[:54] + hash_suffix

        # Ensure minimum length
        if len(safe_name) < 3:
            safe_name = safe_name + '_project'

        return safe_name

    def _get_collection(self, project_id: str):
        """
        Get or create a collection for the specified project.

        Args:
            project_id: The project identifier

        Returns:
            ChromaDB Collection object or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            collection_name = self._get_collection_name(project_id)
            collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"project_id": project_id}
            )
            return collection
        except Exception as e:
            logger.error(f"Failed to get collection for project {project_id}: {str(e)}")
            return None

    def _chunk_content(
        self,
        content: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Split content into overlapping chunks for better retrieval.

        Args:
            content: The text content to chunk
            chunk_size: Target number of words per chunk
            overlap: Number of words to overlap between chunks

        Returns:
            List of text chunks
        """
        # Split into words
        words = content.split()

        if len(words) <= chunk_size:
            return [content] if content.strip() else []

        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)

            if chunk_text.strip():
                chunks.append(chunk_text)

            # Move start forward, accounting for overlap
            start = end - overlap

            # Prevent infinite loop
            if start <= 0:
                start = end

        return chunks

    def _generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """Generate a unique ID for a chunk."""
        return hashlib.md5(f"{file_path}:{chunk_index}".encode()).hexdigest()

    def index_file(
        self,
        project_id: str,
        file_path: str,
        content: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> bool:
        """
        Index a file's content into the project's vector store.

        Args:
            project_id: The project identifier
            file_path: Relative path to the file within the project
            content: The text content to index
            chunk_size: Target number of words per chunk
            overlap: Number of words to overlap between chunks

        Returns:
            True if indexing succeeded, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Memory service unavailable. Skipping indexing for {file_path}")
            return False

        try:
            collection = self._get_collection(project_id)
            if collection is None:
                return False

            # Skip empty content
            if not content or not content.strip():
                logger.debug(f"Skipping empty content for {file_path}")
                return True

            # Skip non-text files based on extension
            text_extensions = {'.md', '.txt', '.markdown', '.rst', '.org'}
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in text_extensions:
                logger.debug(f"Skipping non-text file: {file_path}")
                return True

            # Chunk the content
            chunks = self._chunk_content(content, chunk_size, overlap)

            if not chunks:
                logger.debug(f"No chunks generated for {file_path}")
                return True

            # Delete existing chunks for this file (to handle updates)
            try:
                # Get existing IDs for this file
                existing = collection.get(
                    where={"source": file_path}
                )
                if existing and existing['ids']:
                    collection.delete(ids=existing['ids'])
                    logger.debug(f"Deleted {len(existing['ids'])} existing chunks for {file_path}")
            except Exception as e:
                # Collection might be empty or metadata filter might fail
                logger.debug(f"Could not delete existing chunks: {str(e)}")

            # Prepare data for upserting
            ids = []
            documents = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = self._generate_chunk_id(file_path, i)
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append({
                    "source": file_path,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })

            # Upsert chunks into collection
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            logger.info(f"Indexed {len(chunks)} chunks from {file_path} for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index file {file_path}: {str(e)}")
            return False

    def query_project(
        self,
        project_id: str,
        query_text: str,
        n_results: int = 5
    ) -> str:
        """
        Query the project's memory for relevant content.

        Args:
            project_id: The project identifier
            query_text: The search query
            n_results: Maximum number of results to return

        Returns:
            Formatted string containing relevant text chunks with their sources
        """
        if not self.is_available():
            return "Memory service is not available."

        try:
            collection = self._get_collection(project_id)
            if collection is None:
                return "Could not access project memory."

            # Check if collection has any documents
            count = collection.count()
            if count == 0:
                return "No content has been indexed for this project yet."

            # Query the collection
            results = collection.query(
                query_texts=[query_text],
                n_results=min(n_results, count)
            )

            if not results or not results['documents'] or not results['documents'][0]:
                return "No relevant content found for your query."

            # Format results
            formatted_chunks = []
            for i, (doc, metadata) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0]
            )):
                source = metadata.get('source', 'Unknown')
                chunk_idx = metadata.get('chunk_index', 0)
                total = metadata.get('total_chunks', 1)

                formatted_chunks.append(
                    f"**[Source: {source} (chunk {chunk_idx + 1}/{total})]**\n{doc}"
                )

            return "\n\n---\n\n".join(formatted_chunks)

        except Exception as e:
            logger.error(f"Failed to query project {project_id}: {str(e)}")
            return f"Error searching memory: {str(e)}"

    def delete_file_memory(self, project_id: str, file_path: str) -> bool:
        """
        Delete all memory chunks for a specific file.

        Args:
            project_id: The project identifier
            file_path: The file path to remove from memory

        Returns:
            True if deletion succeeded, False otherwise
        """
        if not self.is_available():
            return False

        try:
            collection = self._get_collection(project_id)
            if collection is None:
                return False

            # Get existing IDs for this file
            existing = collection.get(
                where={"source": file_path}
            )
            if existing and existing['ids']:
                collection.delete(ids=existing['ids'])
                logger.info(f"Deleted {len(existing['ids'])} chunks for {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file memory for {file_path}: {str(e)}")
            return False

    def delete_project_memory(self, project_id: str) -> bool:
        """
        Delete all memory for a project (reset/wipe the collection).

        Args:
            project_id: The project identifier

        Returns:
            True if deletion succeeded, False otherwise
        """
        if not self.is_available():
            return False

        try:
            collection_name = self._get_collection_name(project_id)
            self._client.delete_collection(collection_name)
            logger.info(f"Deleted memory collection for project {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory for project {project_id}: {str(e)}")
            return False

    def reset_project_memory(self, project_id: str) -> bool:
        """
        Reset/wipe the collection for a fresh re-index.
        Alias for delete_project_memory for clearer intent.

        Args:
            project_id: The project identifier

        Returns:
            True if reset succeeded, False otherwise
        """
        return self.delete_project_memory(project_id)

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics about a project's indexed memory.

        Args:
            project_id: The project identifier

        Returns:
            Dictionary with stats like document count, sources, etc.
        """
        if not self.is_available():
            return {"available": False, "error": "Memory service not available"}

        try:
            collection = self._get_collection(project_id)
            if collection is None:
                return {"available": False, "error": "Could not access collection"}

            count = collection.count()

            # Get unique sources
            if count > 0:
                all_data = collection.get()
                sources = set()
                for metadata in all_data.get('metadatas', []):
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])

                return {
                    "available": True,
                    "total_chunks": count,
                    "indexed_files": len(sources),
                    "sources": list(sources)
                }
            else:
                return {
                    "available": True,
                    "total_chunks": 0,
                    "indexed_files": 0,
                    "sources": []
                }

        except Exception as e:
            logger.error(f"Failed to get stats for project {project_id}: {str(e)}")
            return {"available": False, "error": str(e)}


# Singleton instance for application-wide use
_memory_service_instance = None


def get_memory_service(persistence_path: str = "./chroma_db") -> ProjectMemory:
    """
    Get the singleton ProjectMemory instance.

    Args:
        persistence_path: Path for ChromaDB persistence

    Returns:
        ProjectMemory instance
    """
    global _memory_service_instance

    if _memory_service_instance is None:
        _memory_service_instance = ProjectMemory(persistence_path)

    return _memory_service_instance
