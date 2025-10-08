import os
import psutil
import logging
import time
from typing import List, Optional
from datetime import datetime

from open_webui.models.files import Files
from open_webui.retrieval.vector.factory import VECTOR_DB_CLIENT
from open_webui.storage.provider import Storage

log = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, memory_threshold: float = 0.70):
        """
        Initialize memory manager with configurable threshold
        
        Args:
            memory_threshold: Memory usage threshold (0.70 = 70%)
        """
        self.memory_threshold = memory_threshold
        
    def get_memory_usage(self) -> float:
        """Get current system memory usage as percentage"""
        return psutil.virtual_memory().percent / 100.0 *100
    
    def get_cache_usage(self) -> float:
        """Get current cache memory usage as percentage"""
        memory_info = psutil.virtual_memory()
        cache_usage = (memory_info.cached + memory_info.buffers) / memory_info.total
        return cache_usage
    
    def get_oldest_files(self, limit: int = 10) -> List[dict]:
        """
        Get oldest uploaded files from database
        
        Args:
            limit: Number of oldest files to retrieve
            
        Returns:
            List of file records with id, filename, created_at
        """
        try:
            files = Files.get_files()  # Get all files
            if not files:
                return []
            
            # Sort by created_at timestamp (oldest first)
            sorted_files = sorted(files, key=lambda x: x.created_at)
            
            return [
                {
                    "id": file.id,
                    "filename": file.filename,
                    "created_at": file.created_at,
                    "path": file.path,
                    "collection_name": file.meta.get("collection_name")
                }
                for file in sorted_files[:limit]
            ]
        except Exception as e:
            log.error(f"Error getting oldest files: {e}")
            return []
    
    def cleanup_file_and_vectors(self, file_record: dict) -> bool:
        """
        Clean up a single file and its associated vectors
        
        Args:
            file_record: File record dictionary
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            file_id = file_record["id"]
            collection_name = file_record.get("collection_name")
            file_path = file_record.get("path")
            
            log.info(f"Cleaning up file {file_id}: {file_record['filename']}")
            
            # 1. Remove from vector database
            if collection_name:
                try:
                    if VECTOR_DB_CLIENT.has_collection(collection_name):
                        # Delete specific file documents from collection
                        VECTOR_DB_CLIENT.delete(
                            collection_name=collection_name,
                            metadata={"file_id": file_id}
                        )
                        log.info(f"Removed vectors for file {file_id} from collection {collection_name}")
                        
                        # If collection is now empty, delete it
                        result = VECTOR_DB_CLIENT.get(collection_name=collection_name)
                        if not result or not result.documents or not result.documents[0]:
                            VECTOR_DB_CLIENT.delete_collection(collection_name=collection_name)
                            log.info(f"Deleted empty collection {collection_name}")
                            
                except Exception as e:
                    log.error(f"Error removing vectors for file {file_id}: {e}")
            
            # 2. Remove physical file from storage
            if file_path:
                try:
                    Storage.delete_file(file_path)
                    log.info(f"Deleted physical file: {file_path}")
                except Exception as e:
                    log.error(f"Error deleting physical file {file_path}: {e}")
            
            # 3. Remove file record from database
            Files.delete_file_by_id(file_id)
            log.info(f"Deleted file record {file_id} from database")
            
            return True
            
        except Exception as e:
            log.error(f"Error cleaning up file {file_record}: {e}")
            return False
    
    def cleanup_cache_memory(self):
        """Clean up system cache memory"""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # For Linux systems, try to clear page cache (requires sudo)
            try:
                os.system("sync")  # Flush filesystem buffers
                log.info("System cache flushed")
            except Exception as e:
                log.debug(f"Could not flush system cache: {e}")
                
        except Exception as e:
            log.error(f"Error cleaning up cache: {e}")
    
    def perform_memory_cleanup(self, cleanup_count: int = 5) -> dict:
        """
        Perform memory cleanup by removing oldest files
        
        Args:
            cleanup_count: Number of files to clean up
            
        Returns:
            Dictionary with cleanup statistics
        """
        start_memory = self.get_memory_usage()
        start_cache = self.get_cache_usage()
        
        log.info(f"Starting memory cleanup - Current memory: {start_memory:.2%}, Cache: {start_cache:.2%}")
        
        # Get oldest files
        oldest_files = self.get_oldest_files(cleanup_count)
        
        if not oldest_files:
            log.warning("No files found for cleanup")
            return {
                "cleaned_files": 0,
                "memory_before": start_memory,
                "memory_after": start_memory,
                "cache_before": start_cache,
                "cache_after": start_cache,
                "freed_memory": 0
            }
        
        cleaned_files = 0
        for file_record in oldest_files:
            if self.cleanup_file_and_vectors(file_record):
                cleaned_files += 1
                log.info(f"Successfully cleaned up file: {file_record['filename']}")
            else:
                log.error(f"Failed to clean up file: {file_record['filename']}")
        
        # Clean up cache memory
        self.cleanup_cache_memory()
        
        # Wait a moment for cleanup to take effect
        time.sleep(2)
        
        end_memory = self.get_memory_usage()
        end_cache = self.get_cache_usage()
        
        freed_memory = start_memory - end_memory
        
        log.info(f"Memory cleanup completed - Cleaned {cleaned_files} files")
        log.info(f"Memory: {start_memory:.2%} -> {end_memory:.2%} (freed: {freed_memory:.2%})")
        log.info(f"Cache: {start_cache:.2%} -> {end_cache:.2%}")
        
        return {
            "cleaned_files": cleaned_files,
            "memory_before": start_memory,
            "memory_after": end_memory,
            "cache_before": start_cache,
            "cache_after": end_cache,
            "freed_memory": freed_memory
        }
    
    def check_and_cleanup_memory(self) -> Optional[dict]:
        """
        Check memory usage and cleanup if threshold exceeded
        
        Returns:
            Cleanup statistics if cleanup performed, None otherwise
        """
        current_memory = self.get_memory_usage()
        current_cache = self.get_cache_usage()
        
        log.debug(f"Memory check - Memory: {current_memory:.2%}, Cache: {current_cache:.2%}, Threshold: {self.memory_threshold:.2%}")
        
        # Check if memory threshold is exceeded
        if current_memory > self.memory_threshold or current_cache > self.memory_threshold:
            log.warning(f"Memory threshold exceeded - Memory: {current_memory:.2%}, Cache: {current_cache:.2%}")
            
            # Calculate how many files to clean based on memory usage
            excess_memory = max(current_memory - self.memory_threshold, current_cache - self.memory_threshold)
            cleanup_count = max(1, int(excess_memory * 20))  # Scale cleanup count with excess memory
            
            return self.perform_memory_cleanup(cleanup_count)
        
        return None

# Global memory manager instance
memory_manager = MemoryManager()