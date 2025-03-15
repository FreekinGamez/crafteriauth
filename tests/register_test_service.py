from backend import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("register_test_service")

def register_test_service():
    """Register the test service in the database with a known API key"""
    
    # Initialize database
    if not db.init_db():
        logger.error("Failed to initialize database")
        return False
        
    # Check if test service already exists
    query = "SELECT id FROM registered_services WHERE domain = %s OR client_secret = %s"
    existing = db.execute_query(
        query, 
        ('localhost:5001', 'niggas123'),
        fetchone=True
    )
    
    if existing:
        logger.info("Test service already exists in database")
        
        # Update the client_secret to ensure it matches
        update_query = """
        UPDATE registered_services 
        SET client_secret = %s, is_active = TRUE
        WHERE id = %s
        RETURNING id
        """
        result = db.execute_query(
            update_query,
            ('niggas123', existing[0]),
            fetchone=True,
            commit=True
        )
        logger.info(f"Updated test service API key, ID: {result[0]}")
        return True
    
    # Create new test service
    insert_query = """
    INSERT INTO registered_services 
    (name, domain, client_id, client_secret, is_active)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """
    
    result = db.execute_query(
        insert_query,
        ('Test Service', 'localhost:5001', '12345678-1234-1234-1234-123456789012', 'niggas123', True),
        fetchone=True,
        commit=True
    )
    
    if result:
        logger.info(f"Created test service with ID: {result[0]}")
        return True
    else:
        logger.error("Failed to create test service")
        return False

if __name__ == "__main__":
    if register_test_service():
        print("✅ Test service registered successfully with API key 'niggas123'")
        print("You can now run the test service and it should be able to verify tokens")
    else:
        print("❌ Failed to register test service")
