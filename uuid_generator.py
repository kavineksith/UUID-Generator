import uuid
import sqlite3
import time
from datetime import datetime
import logging
import argparse
import json
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, Dict, Any

# Custom Exceptions
class UUIDGenerationError(Exception):
    """Base exception for UUID generation errors"""
    def __init__(self, message, error_code = None):
        super().__init__(message, error_code)

class DatabaseError(UUIDGenerationError):
    """Database-related errors"""
    def __init__(self, message, error_code = None):
        super().__init__(message, error_code)

class InputValidationError(UUIDGenerationError):
    """Invalid input parameters"""
    def __init__(self, message, error_code = None):
        super().__init__(message, error_code)

class DuplicateUUIDError(UUIDGenerationError):
    """Duplicate UUID detected"""
    def __init__(self, message, error_code = None):
        super().__init__(message, error_code)

# Configure advanced logging
def setup_logger():
    logger = logging.getLogger('UUIDGenerator')
    logger.setLevel(logging.DEBUG)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'uuid_generator.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

class UUIDGenerator:
    """Production-ready UUID generator with database storage and validation"""
    
    def __init__(self, db_path: str = 'uuids.db'):
        """Initialize the UUID generator with database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS uuids (
                        uuid TEXT PRIMARY KEY,
                        uuid_type TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        category TEXT,
                        additional_info TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_uuid_type ON uuids(uuid_type)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_category ON uuids(category)
                ''')
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")

    def _store_uuid(self, uuid_str: str, uuid_type: str, category: Optional[str] = None, 
                   additional_info: Optional[Dict[str, Any]] = None) -> bool:
        """Store a generated UUID in the database
        
        Args:
            uuid_str: The generated UUID string
            uuid_type: Type of UUID (v1, v4, timestamp, etc.)
            category: Optional category for the UUID
            additional_info: Optional additional metadata as a dictionary
            
        Returns:
            bool: True if storage was successful, False otherwise
            
        Raises:
            DuplicateUUIDError: If the UUID already exists in the database
            DatabaseError: For other database-related issues
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for duplicate UUID
                cursor.execute('SELECT uuid FROM uuids WHERE uuid = ?', (uuid_str,))
                if cursor.fetchone():
                    raise DuplicateUUIDError(f"UUID {uuid_str} already exists in database")
                
                # Insert new UUID
                cursor.execute('''
                    INSERT INTO uuids (uuid, uuid_type, timestamp, category, additional_info)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    uuid_str,
                    uuid_type,
                    datetime.utcnow().isoformat(),
                    category,
                    str(additional_info) if additional_info else None
                ))
                conn.commit()
                return True
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error storing UUID: {str(e)}")
            raise DuplicateUUIDError(f"UUID {uuid_str} already exists in database")
        except sqlite3.Error as e:
            logger.error(f"Database error storing UUID: {str(e)}")
            raise DatabaseError(f"Failed to store UUID: {str(e)}")

    def _validate_category(self, category: Optional[str]) -> bool:
        """Validate the category parameter
        
        Args:
            category: Category string to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            InputValidationError: If category is invalid
        """
        if category is None:
            return True
            
        if not isinstance(category, str):
            raise InputValidationError("Category must be a string or None")
            
        if len(category) > 50:
            raise InputValidationError("Category must be 50 characters or less")
            
        return True

    def generate_v1(self, category: Optional[str] = None) -> str:
        """Generate a version 1 UUID (time-based)
        
        Args:
            category: Optional category for the UUID
            
        Returns:
            str: The generated UUID
            
        Raises:
            UUIDGenerationError: If generation fails
        """
        try:
            self._validate_category(category)
            uuid_str = str(uuid.uuid1())
            self._store_uuid(uuid_str, 'v1', category)
            logger.info(f"Generated v1 UUID: {uuid_str}")
            return uuid_str
        except Exception as e:
            logger.error(f"Failed to generate v1 UUID: {str(e)}")
            raise UUIDGenerationError(f"Failed to generate v1 UUID: {str(e)}")
        
    """
        Add uuid v3 and v5 types for this section to enhance the productivity
    """

    def generate_v4(self, category: Optional[str] = None) -> str:
        """Generate a version 4 UUID (random)
        
        Args:
            category: Optional category for the UUID
            
        Returns:
            str: The generated UUID
            
        Raises:
            UUIDGenerationError: If generation fails
        """
        try:
            self._validate_category(category)
            uuid_str = str(uuid.uuid4())
            self._store_uuid(uuid_str, 'v4', category)
            logger.info(f"Generated v4 UUID: {uuid_str}")
            return uuid_str
        except Exception as e:
            logger.error(f"Failed to generate v4 UUID: {str(e)}")
            raise UUIDGenerationError(f"Failed to generate v4 UUID: {str(e)}")

    def generate_timestamp_uuid(self, prefix: Optional[str] = None, 
                              category: Optional[str] = None) -> str:
        """Generate a timestamp-based UUID with optional prefix
        
        Args:
            prefix: Optional prefix for the UUID (max 5 chars)
            category: Optional category for the UUID
            
        Returns:
            str: The generated timestamp UUID
            
        Raises:
            InputValidationError: If prefix is invalid
            UUIDGenerationError: If generation fails
        """
        try:
            self._validate_category(category)
            
            if prefix is not None:
                if not isinstance(prefix, str):
                    raise InputValidationError("Prefix must be a string or None")
                if len(prefix) > 5:
                    raise InputValidationError("Prefix must be 5 characters or less")
                if not prefix.isalnum():
                    raise InputValidationError("Prefix must be alphanumeric")
                prefix = prefix.upper()
            
            # Get current timestamp in microseconds
            timestamp = int(time.time() * 1_000_000)
            
            # Generate the UUID
            if prefix:
                uuid_str = f"{prefix}-{timestamp:X}"
            else:
                uuid_str = f"{timestamp:X}"
                
            # Store the UUID
            additional_info = {'prefix': prefix} if prefix else None
            self._store_uuid(uuid_str, 'timestamp', category, additional_info)
            
            logger.info(f"Generated timestamp UUID: {uuid_str}")
            return uuid_str
            
        except InputValidationError as e:
            logger.error(f"Input validation failed for timestamp UUID: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate timestamp UUID: {str(e)}")
            raise UUIDGenerationError(f"Failed to generate timestamp UUID: {str(e)}")

    def check_duplicate(self, uuid_str: str) -> bool:
        """Check if a UUID exists in the database
        
        Args:
            uuid_str: UUID to check
            
        Returns:
            bool: True if UUID exists, False otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT uuid FROM uuids WHERE uuid = ?', (uuid_str,))
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Database error checking duplicate UUID: {str(e)}")
            raise DatabaseError(f"Failed to check duplicate UUID: {str(e)}")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about generated UUIDs
        
        Returns:
            dict: Statistics with counts by type and category
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count by UUID type
                cursor.execute('SELECT uuid_type, COUNT(*) FROM uuids GROUP BY uuid_type')
                stats['by_type'] = dict(cursor.fetchall())
                
                # Count by category
                cursor.execute('''
                    SELECT category, COUNT(*) 
                    FROM uuids 
                    WHERE category IS NOT NULL
                    GROUP BY category
                ''')
                stats['by_category'] = dict(cursor.fetchall())
                
                # Total count
                cursor.execute('SELECT COUNT(*) FROM uuids')
                stats['total'] = cursor.fetchone()[0]
                
                return stats
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting statistics: {str(e)}")
            raise DatabaseError(f"Failed to get statistics: {str(e)}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='UUID Generator Client')
    parser.add_argument('--type', choices=['v1', 'v4', 'timestamp'], required=True,
                       help='Type of UUID to generate')
    parser.add_argument('--category', help='Optional category for the UUID')
    parser.add_argument('--prefix', help='Prefix for timestamp UUIDs (max 5 chars)')
    parser.add_argument('--stats', action='store_true', 
                       help='Get statistics instead of generating a UUID')
    
    args = parser.parse_args()
    
    generator = UUIDGenerator()
    
    try:
        if args.stats:
            # Display statistics
            stats = generator.get_stats()
            print("UUID Statistics:")
            print(json.dumps(stats, indent=2))
        else:
            # Generate UUID based on type
            if args.type == 'v1':
                uuid_str = generator.generate_v1(args.category)
            elif args.type == 'v4':
                uuid_str = generator.generate_v4(args.category)
            elif args.type == 'timestamp':
                uuid_str = generator.generate_timestamp_uuid(args.prefix, args.category)
            
            print(f"Generated UUID: {uuid_str}")
            
    except InputValidationError as e:
        print(f"Input validation error: {str(e)}")
    except UUIDGenerationError as e:
        print(f"UUID generation failed: {str(e)}")

if __name__ == '__main__':
    main()
