#!/usr/bin/env python3
"""
Migration script to populate the observations table with data from S3.
This script extracts observation data from existing S3 paths and populates the RDS observations table.
"""

import sys
import time
from typing import List, Tuple, Optional
from tqdm import tqdm

# Import local modules
from config import config
from db.clients.rds_storage_client import RdsStorageClient
from db.shared_repositories import observations_repository
from models.observation import Observation, ObservationORM
import utils.observations_sub_bucket as observations_sub_bucket
from utils.opensearch import AdQuery


def parse_ad_path_from_s3_key(s3_key: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse an S3 key to extract observer_id, timestamp, and ad_id.
    
    Expected format: observer_id/temp/timestamp.ad_id/
    or observer_id/rdo/timestamp.ad_id/output.json
    
    Args:
        s3_key (str): The S3 key to parse
        
    Returns:
        Tuple[observer_id, timestamp, ad_id] or None if parsing fails
    """
    try:
        # Remove trailing slash and split by /
        parts = s3_key.rstrip('/').split('/')
        
        if len(parts) < 3:
            return None
            
        observer_id = parts[0]
        
        # Look for patterns like "timestamp.ad_id" in various subdirectories
        timestamp_ad_part = None
        for part in parts[1:]:
            if '.' in part and not part.endswith('.json'):
                timestamp_ad_part = part
                break
        
        if not timestamp_ad_part:
            return None
        
        # Split timestamp.ad_id
        timestamp_ad_split = timestamp_ad_part.split('.')
        if len(timestamp_ad_split) < 2:
            return None
            
        timestamp = timestamp_ad_split[0]
        ad_id = '.'.join(timestamp_ad_split[1:])  # In case ad_id contains dots
        
        return observer_id, timestamp, ad_id
        
    except Exception as e:
        print(f"Error parsing S3 key {s3_key}: {e}")
        return None


def list_all_rdo_paths() -> List[str]:
    """
    List all RDO output.json files from S3.
    
    Returns:
        List of S3 keys for RDO output files
    """
    print("Scanning S3 for RDO output files...")
    
    # Use list_dir with recursive listing to find all RDO output files
    all_paths = AdQuery().query_all({
        "method": "ALL"
    }, page_size=10000)
    
    all_paths = [
        path.replace("temp/", "rdo/") + "/output.json"
        for path in all_paths
    ]
    
    print(f"Found {len(all_paths)} RDO output files")
    return all_paths


def extract_observations() -> List[Observation]:
    """
    Extract observation data from available RDOs.
    
    Returns:
        List of Observation objects
    """
    rdo_paths = list_all_rdo_paths()
    observations = []
    
    print("Extracting observations from S3 paths...")
    
    for rdo_path in tqdm(rdo_paths, desc="Processing RDO paths"):
        parsed = parse_ad_path_from_s3_key(rdo_path)
        if parsed:
            observer_id, timestamp_str, ad_id = parsed
            
            try:
                timestamp = int(timestamp_str)
                
                observation = Observation(
                    observer_id=observer_id,
                    observation_id=ad_id,
                    timestamp=timestamp,
                )
                observations.append(observation)
                
            except ValueError as e:
                print(f"Error converting timestamp '{timestamp_str}' for {rdo_path}: {e}")
                continue
        else:
            print(f"Could not parse path: {rdo_path}")
    
    print(f"Extracted {len(observations)} observations")
    return observations


def clear_observations_table() -> None:
    """Clear the observations table in RDS.
    This is useful for ensuring a clean state before migration.
    """
    print("Clearing observations table...")
    
    try:
        rds_client: RdsStorageClient = observations_repository._client
        rds_client.connect()
        
        with rds_client.session_maker() as session:
            session.query(ObservationORM).delete()
            session.commit()
        
        print("Observations table cleared successfully")
    except Exception as e:
        print(f"Error clearing observations table: {e}")
    finally:
        rds_client.disconnect()

def populate_observations_table(observations: List[Observation]) -> None:
    """
    Populate the observations table with the extracted observations.
    
    Args:
        observations: List of Observation objects to insert
    """
    print("Populating observations table...")
    
    rds_client: RdsStorageClient = observations_repository._client
    rds_client.connect()
    
    observations_orm = [
        ObservationORM(
            observation_id=obs.observation_id,
            observer_id=obs.observer_id,
            timestamp=int(obs.timestamp)
        ) for obs in observations
    ]
    
    try:
        with rds_client.session_maker() as session:
            session.add_all(observations_orm)
            session.commit()
        print(f"Inserted {len(observations)} observations into RDS")
    except Exception as e:
        raise e
        print(f"Error inserting observations: {e}")
    finally:
        rds_client.disconnect()
    
    print(f"Populated observations table with {len(observations)} records")
    print("Migration completed successfully!")

def verify_migration() -> None:
    """
    Verify the migration by checking the observations table.
    """
    print("Verifying migration...")
    
    try:
        with observations_repository.create_session() as session:
            observations: list[Observation] = session.list()
            print(f"Total observations in database: {len(observations)}")
            
            if observations:
                # Show some sample data
                print("Sample observations:")
                for obs_dict in observations[:5]:
                    print(f"  {obs_dict.observer_id}/{obs_dict.timestamp}.{obs_dict.observation_id}")
            
    except Exception as e:
        print(f"Error verifying migration: {e}")


def main():
    """
    Main migration function.
    """
    print("Starting observations migration from S3 to RDS...")
    print(f"Target database: {config.postgres.database}")
    
    # Clear the observations table to ensure a clean state
    clear_observations_table()
    
    # Extract observations from S3
    observations = extract_observations()
    
    if not observations:
        print("No observations found. Migration aborted.")
        return
    
    # Remove duplicates based on observation_id
    unique_observations = {}
    for obs in observations:
        unique_observations[obs.observation_id] = obs
    
    observations = list(unique_observations.values())
    print(f"After deduplication: {len(observations)} unique observations")
    
    # Populate the database
    populate_observations_table(observations)
    
    # Verify the migration
    verify_migration()
    
    print("Migration completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_migration()
    else:
        main()
