import os
import logging
import time
import warnings

from pymongo import MongoClient
from urllib.parse import quote_plus

warnings.filterwarnings("ignore", message=".*CosmosDB.*")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_mongo_status(collection=None):
    """
    Checks the status of MongoDB in a way compatible with Atlas
    - Database stats
    - Index information
    - Response time

    Args:
        collection: MongoDB collection to check (default: None, which checks just database status)

    Returns information that can help diagnose timeouts and performance issues.
    """
    logger.info("Checking MongoDB status...")

    try:
        # Get collection stats if a collection was provided
        if collection is not None:
            collection_name = collection.name
            logger.info(f"Checking collection stats for {collection_name}...")
            try:
                stats = db.command("collStats", collection_name)
                logger.info(f"Collection stats for {collection_name}:")
                logger.info(f"  - Document count: {stats.get('count', 'N/A')}")
                logger.info(f"  - Size: {stats.get('size', 0) / (1024 * 1024):.2f} MB")
                logger.info(
                    f"  - Storage size: {stats.get('storageSize', 0) / (1024 * 1024):.2f} MB"
                )
                logger.info(f"  - Index count: {len(stats.get('indexSizes', {}))}")
                total_index_size = (
                    sum(stats.get("indexSizes", {}).values()) / (1024 * 1024)
                    if stats.get("indexSizes")
                    else 0
                )
                logger.info(f"  - Total index size: {total_index_size:.2f} MB")

                # List indexes and their details
                logger.info(f"Checking indexes for {collection_name}...")
                try:
                    indexes = list(collection.list_indexes())
                    logger.info(
                        f"Found {len(indexes)} indexes in {collection_name} collection:"
                    )
                    for idx in indexes:
                        idx_name = idx.get("name", "unnamed")
                        idx_keys = idx.get("key", {})
                        idx_size = (
                            stats.get("indexSizes", {}).get(idx_name, 0) / (1024 * 1024)
                            if stats.get("indexSizes")
                            else 0
                        )
                        logger.info(
                            f"  - Index '{idx_name}': {idx_keys} (Size: {idx_size:.2f} MB)"
                        )
                except Exception as e:
                    logger.info(f"Could not retrieve index information: {e}")
            except Exception as e:
                logger.info(
                    f"Could not retrieve collection stats for {collection_name}: {e}"
                )

        # Check for ongoing operations (with proper method)
        logger.info("Checking for ongoing operations...")
        try:
            # This is the correct way to get currentOp from Atlas
            admin_db = client.admin
            current_ops = admin_db.command("currentOp")

            # Filter for operations running more than 5 seconds
            ongoing_ops = [
                op
                for op in current_ops.get("inprog", [])
                if op.get("secs_running", 0) > 5
            ]

            if ongoing_ops:
                logger.info(f"Found {len(ongoing_ops)} long-running operations:")
                for op in ongoing_ops:
                    op_type = op.get("op", "unknown")
                    ns = op.get("ns", "unknown")
                    running_time = op.get("secs_running", 0)

                    logger.info(f"  - {op_type} on {ns} running for {running_time}s")

                    # Check if this is an index build
                    if op_type == "command" and "createIndexes" in str(op):
                        logger.warning(
                            f"    Index build in progress! This could be causing timeouts."
                        )
            else:
                logger.info("No long-running operations found.")
        except Exception as e:
            logger.info(f"Could not check for ongoing operations: {e}")

        # Try to ping the database to check response time
        logger.info("Checking database response time...")
        try:
            start_time = time.time()
            db.command("ping")
            response_time = time.time() - start_time
            logger.info(f"Database ping response time: {response_time*1000:.2f} ms")

            if response_time > 1.0:
                logger.warning(
                    "Database response time is high (>1 second), which could indicate performance issues"
                )
        except Exception as e:
            logger.error(f"Could not ping database: {e}")

        logger.info("MongoDB status check completed.")
        return True

    except Exception as e:
        logger.error(f"Error checking MongoDB status: {e}")
        return False


# Function to list all collections in the database
def list_collections():
    """
    Lists all collections in the database
    """
    try:
        collections = db.list_collection_names()
        logger.info(f"Found {len(collections)} collections in database '{db.name}':")
        for collection in collections:
            logger.info(f"  - {collection}")
    except Exception as e:
        logger.error(f"Error listing collections: {e}")


# Function to create indexes safely with consistent approach
def ensure_indexes(collection, indexes):
    """
    Creates indexes if they don't already exist

    Args:
        collection: MongoDB collection
        indexes: List of key patterns as lists of tuples [[(field, direction), ...], ...]
    """
    existing_index_keys = []

    # Get existing indexes
    try:
        existing_indexes = list(collection.list_indexes())
        logger.info(
            f"Found {len(existing_indexes)} existing indexes in {collection.name}"
        )

        # Extract the keys from existing indexes
        for idx in existing_indexes:
            # Skip the _id index
            if idx["name"] == "_id_":
                continue

            key_pattern = [(k, v) for k, v in idx["key"].items()]
            existing_index_keys.append(tuple(key_pattern))
            logger.info(f"  - {idx['name']}: {key_pattern}")
    except Exception as e:
        logger.error(f"Error listing existing indexes: {e}")
        return

    # Create new indexes
    created_count = 0
    for key_pattern in indexes:
        # Convert to tuple for comparison
        key_tuple = tuple(key_pattern)

        # Check if index already exists
        if key_tuple in existing_index_keys:
            logger.info(f"Index {key_pattern} already exists, skipping")
            continue

        # Create the index with background option always enabled
        try:
            collection.create_index(key_pattern, background=True)
            created_count += 1
            logger.info(f"Created index {key_pattern}")
        except Exception as e:
            logger.error(f"Error creating index {key_pattern}: {e}")

    logger.info(f"Created {created_count} new indexes in {collection.name}")


def delete_index(collection, index_identifier):
    """
    Deletes an index by name or key pattern.

    Args:
        collection: MongoDB collection
        index_identifier: Either the name of the index (string) or
                          the key pattern of the index (list of tuples)

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # If index_identifier is already a string, assume it's an index name
        if isinstance(index_identifier, str):
            index_name = index_identifier
        # If it's a list of tuples, convert to index name format
        elif isinstance(index_identifier, list):
            # Convert the list of tuples to the MongoDB naming convention
            index_parts = []
            for key, direction in index_identifier:
                index_parts.append(f"{key}_{direction}")
            index_name = "_".join(index_parts)
        else:
            logger.error(f"Invalid index identifier type: {type(index_identifier)}")
            return False

        # Drop the index
        collection.drop_index(index_name)
        logger.info(f"Successfully deleted index '{index_name}' from {collection.name}")
        return True

    except Exception as e:
        logger.error(f"Error deleting index: {e}")
        return False


def delete_collection(collection_name):
    """
    Deletes a collection from the database.

    Args:
        collection_name: Name of the collection to delete (string)

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Check if collection exists first
        collections = db.list_collection_names()
        if collection_name not in collections:
            logger.warning(
                f"Collection '{collection_name}' does not exist, skipping deletion"
            )
            return False

        # Drop the collection
        db.drop_collection(collection_name)
        logger.info(f"Successfully deleted collection '{collection_name}'")
        return True

    except Exception as e:
        logger.error(f"Error deleting collection '{collection_name}': {e}")
        return False


def create_indexes():
    logger.info("Starting index creation process...")

    # Define the indexes we want to ensure exist (using consistent list of tuples format)
    # Chat Log indexes
    chat_log_indexes = [
        [("created_on", 1)],
        [("session_id", 1)],
        [("message_id", 1)],
        [("user_hash", 1)],
    ]

    # Search Log indexes
    search_log_indexes = [
        [("created_on", 1)],
        [("message_id", 1)],
    ]

    # Debug Log indexes
    debug_log_indexes = [
        [("created_on", 1)],
        [("message_id", 1)],
    ]

    # Appraisal Log indexes
    appraisal_log_indexes = [
        [("created_on", 1)],
        [("message_id", 1)],
    ]

    # Action Log indexes
    action_log_indexes = [
        [("created_on", 1)],
    ]

    # Create the indexes
    ensure_indexes(chat_log_collection, chat_log_indexes)
    ensure_indexes(search_log_collection, search_log_indexes)
    ensure_indexes(debug_log_collection, debug_log_indexes)
    ensure_indexes(appraisal_log_collection, appraisal_log_indexes)
    ensure_indexes(action_log_collection, action_log_indexes)

    logger.info("Index creation process completed")


def delete_indexes():
    """
    Deletes the selected list of indexes
    """
    logger.info("Starting index deletion process...")

    # Define the indexes we want to delete (using consistent list of tuples format)
    indexes_to_delete = []

    # Delete the indexes
    for index in indexes_to_delete:
        delete_index(chat_log_collection, index)

    logger.info("Index deletion process completed")


def delete_collections():
    """
    Deletes the selected list of collections
    """
    logger.info("Starting collection deletion process...")

    # Define the collections you want to delete
    collections_to_delete = []

    # Delete the collections
    deleted_count = 0
    for collection_name in collections_to_delete:
        if delete_collection(collection_name):
            deleted_count += 1

    logger.info(
        f"Collection deletion process completed. Deleted {deleted_count} collections."
    )


# Initialize MongoDB client
def get_db_connection():
    # Connection details
    username = os.getenv("MONGO_USER")
    host = os.getenv("MONGO_HOST")
    password = os.getenv("MONGO_PASS")
    encoded_password = quote_plus(password)

    # Connection string
    connection_string = f"mongodb+srv://{username}:{encoded_password}@{host}/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"

    # Initialize MongoDB client
    client = MongoClient(connection_string)
    db = client["rubicon"]
    return client, db


# Create clients and collections at module level for use in import scenarios
client, db = get_db_connection()
chat_log_collection = db["chat_log"]
search_log_collection = db["search_log"]
debug_log_collection = db["debug_log"]
appraisal_log_collection = db["appraisal_log"]
action_log_collection = db["action_log"]

# Only run index creation when script is executed directly
if __name__ == "__main__":
    # Uncomment to create indexes
    create_indexes()
    # delete_indexes()
    # delete_collections()

    # Check MongoDB Server Version
    logger.info("Checking MongoDB version...")
    try:
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        logger.info(f"MongoDB version: {version}")
    except Exception as e:
        logger.error(f"Could not retrieve MongoDB version: {e}")

    print("\n----------------------------------------------------------------------")

    # List all collections in the database
    logger.info("Listing all collections in database...")
    list_collections()

    print("\n----------------------------------------------------------------------")

    # Check chat_log collection
    check_mongo_status(chat_log_collection)

    print("\n----------------------------------------------------------------------")

    # Check search_log collection
    check_mongo_status(search_log_collection)

    print("\n----------------------------------------------------------------------")

    # Check debug_log collection
    check_mongo_status(debug_log_collection)

    print("\n----------------------------------------------------------------------")

    # Check appraisal_log collection
    check_mongo_status(appraisal_log_collection)

    print("\n----------------------------------------------------------------------")

    # Check action_log collection
    check_mongo_status(action_log_collection)

    print("\n----------------------------------------------------------------------")

    # Just check general DB status (no collection stats)
    check_mongo_status()
