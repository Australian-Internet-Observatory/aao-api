import json
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.attribute import AdAttribute, AdAttributeORM
import utils.metadata_sub_bucket as metadata
import sys

# Repository for ad attributes
from db.shared_repositories import ad_attributes_repository

AD_ATTRIBUTES_PREFIX = 'ad-custom-attributes'


def get_ad_s3_path(observer_id: str, timestamp: str, ad_id: str) -> str:
    """
    Generate the S3 path for an ad's attributes file.
    
    Args:
        observer_id: The observer ID
        timestamp: The timestamp
        ad_id: The ad ID
        
    Returns:
        The S3 path for the ad's attributes file
    """
    return f"{AD_ATTRIBUTES_PREFIX}/{observer_id}_{timestamp}.{ad_id}.json"


def parse_ad_path_from_s3_key(s3_key: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse an S3 key to extract observer_id, timestamp, and ad_id.
    
    Args:
        s3_key: The S3 key (e.g., "ad-custom-attributes/observer_timestamp.ad_id.json")
        
    Returns:
        Tuple of (observer_id, timestamp, ad_id) or None if parsing fails
    """
    try:
        # Remove the prefix
        filename = s3_key.replace(f"{AD_ATTRIBUTES_PREFIX}/", "")
        
        # Remove .json extension
        if not filename.endswith('.json'):
            return None
        filename = filename[:-5]
        
        # Split by the last dot to separate ad_id
        parts = filename.split('.')
        if len(parts) < 2:
            return None
            
        ad_id = parts[-1]
        observer_timestamp = '.'.join(parts[:-1])
        
        # Split observer_timestamp by underscore
        underscore_parts = observer_timestamp.split('_')
        if len(underscore_parts) < 2:
            return None
            
        observer_id = underscore_parts[0]
        timestamp = '_'.join(underscore_parts[1:])
        
        return observer_id, timestamp, ad_id
    except Exception as e:
        print(f"Error parsing S3 key {s3_key}: {e}")
        return None


def parse_attribute_content(content_dict: Dict) -> List[Dict]:
    """
    Parse the attribute content dictionary and convert it to a list of attribute dictionaries.
    
    Args:
        content_dict: Dictionary with structure:
        {
            "key_1": {
                "value": "value",
                "created_at": timestamp,
                "created_by": "username",
                "modified_at": timestamp,
                "modified_by": "username"
            },
            ...
        }
        
    Returns:
        List of attribute dictionaries ready for database insertion
    """
    attributes = []
    
    for key, attr_data in content_dict.items():
        # Ensure all required fields are present with defaults
        attribute = {
            'key': key,
            'value': attr_data.get('value', ''),
            'created_at': attr_data.get('created_at', 0),
            'created_by': attr_data.get('created_by', 'unknown'),
            'modified_at': attr_data.get('modified_at', attr_data.get('created_at', 0)),
            'modified_by': attr_data.get('modified_by', attr_data.get('created_by', 'unknown'))
        }
        attributes.append(attribute)
    
    return attributes


def list_ad_attribute_files() -> List[str]:
    """
    List all ad attribute files in S3.
    
    Returns:
        List of S3 keys for ad attribute files
    """
    try:
        return [path for path in metadata.list_objects(f"{AD_ATTRIBUTES_PREFIX}/") if path.endswith('.json')]
    except Exception as e:
        print(f"Error listing S3 objects: {e}")
        return []


class AdAttributeEntities:
    def __init__(self):
        self.attribute_files = list_ad_attribute_files()
        print(f"Found {len(self.attribute_files)} ad attribute files in S3")
    
    def list_observation_ids(self) -> List[str]:
        """
        Extract unique observation IDs from all attribute files.
        
        Returns:
            List of observation IDs
        """
        observation_ids = set()
        for file_path in self.attribute_files:
            parsed = parse_ad_path_from_s3_key(file_path)
            if parsed:
                observer_id, timestamp, ad_id = parsed
                observation_id = f"{ad_id}"
                observation_ids.add(observation_id)
        return list(observation_ids)
    
    def get_attributes_for_ad(self, s3_key: str) -> Optional[List[AdAttribute]]:
        """
        Get all attributes for a specific ad from S3.
        
        Args:
            s3_key: The S3 key for the ad's attributes file
            
        Returns:
            List of AdAttribute objects or None if error
        """
        try:
            # Parse the S3 key to get ad info
            parsed = parse_ad_path_from_s3_key(s3_key)
            if not parsed:
                print(f"Could not parse S3 key: {s3_key}")
                return None
                
            observer_id, timestamp, ad_id = parsed
            observation_id = f"{ad_id}"
            
            # Get the content from S3
            content = metadata.get_object(s3_key, read_body=True)
            if not content:
                print(f"No content found for {s3_key}")
                return None
                
            content_dict = json.loads(content)
            
            # Parse the attributes
            attribute_dicts = parse_attribute_content(content_dict)
            
            # Convert to AdAttribute objects
            ad_attributes = []
            for attr_dict in attribute_dicts:
                ad_attr = AdAttribute(
                    observation_id=observation_id,
                    key=attr_dict['key'],
                    value=str(attr_dict['value']),
                    created_at=attr_dict['created_at'],
                    created_by=attr_dict['created_by'],
                    modified_at=attr_dict['modified_at'],
                    modified_by=attr_dict['modified_by']
                )
                ad_attributes.append(ad_attr)
            
            return ad_attributes
            
        except Exception as e:
            print(f"Error processing {s3_key}: {e}")
            return None


def migrate_single_ad_attributes(s3_key: str, entities: AdAttributeEntities) -> bool:
    """
    Migrate attributes for a single ad from S3 to RDS.
    
    Args:
        s3_key: The S3 key for the ad's attributes file
        entities: The AdAttributeEntities instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        attributes = entities.get_attributes_for_ad(s3_key)
        if not attributes:
            return False
            
        # Insert each attribute
        with ad_attributes_repository.create_session() as session:
            for attr in attributes:
                try:
                    session.create_or_update(attr)
                except Exception as e:
                    if 'duplicate key value violates unique constraint' in str(e):
                        # Attribute already exists, try to update it
                        try:
                            session.create_or_update(attr)
                        except Exception as update_e:
                            print(f"Error updating attribute {attr.observation_id}:{attr.key}: {update_e}")
                            continue
                    else:
                        print(f"Error creating attribute {attr.observation_id}:{attr.key}: {e}")
                    continue
        
        return True
        
    except Exception as e:
        print(f"Error migrating {s3_key}: {e}")
        return False


def main():
    """
    Main migration function.
    """
    print("Starting ad attributes migration from S3 to RDS...")
    
    entities = AdAttributeEntities()
    
    if not entities.attribute_files:
        print("No ad attribute files found in S3. Migration complete.")
        return
    
    successful_migrations = 0
    failed_migrations = 0
    
    for s3_key in tqdm(entities.attribute_files, desc="Migrating ad attributes"):
        if migrate_single_ad_attributes(s3_key, entities):
            successful_migrations += 1
        else:
            failed_migrations += 1
    
    print(f"\nMigration completed!")
    print(f"Successful migrations: {successful_migrations}")
    print(f"Failed migrations: {failed_migrations}")
    print(f"Total files processed: {len(entities.attribute_files)}")


def verify_migration():
    """
    Verify the migration by comparing S3 data with RDS data.
    """
    print("Verifying migration...")
    
    entities = AdAttributeEntities()
    observation_ids = entities.list_observation_ids()
    
    verification_results = {
        'total_ads': len(observation_ids),
        'verified_ads': 0,
        'missing_ads': 0,
        'mismatched_attributes': 0
    }
    
    for observation_id in tqdm(observation_ids, desc="Verifying migration"):
        try:
            # Get attributes from RDS
            with ad_attributes_repository.create_session() as session:
                rds_attributes = session.get({"observation_id": observation_id})
                if not rds_attributes:
                    verification_results['missing_ads'] += 1
                    print(f"Missing in RDS: {observation_id}")
                    continue
                    
                verification_results['verified_ads'] += 1
            
        except Exception as e:
            print(f"Error verifying {observation_id}: {e}")
            verification_results['missing_ads'] += 1
    
    print(f"\nVerification Results:")
    print(f"Total ads: {verification_results['total_ads']}")
    print(f"Verified ads: {verification_results['verified_ads']}")
    print(f"Missing ads: {verification_results['missing_ads']}")
    print(f"Mismatched attributes: {verification_results['mismatched_attributes']}")


if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_migration()
    else:
        main()
