#!/usr/bin/env python3
"""
ETL script for processing clip classification data from S3 and storing it in RDS.

This script reads clip classification JSON files from the S3 bucket 
(fta-mobile-observations-v2/{observer_uuid}/clip_classifications/{observation_uuid}.json)
and stores the composite classification data in the ad_classifications RDS table.
"""

import json
import time
from typing import List, Optional
from uuid import uuid4
from tqdm import tqdm

from config import config
from db.clients.rds_storage_client import RdsStorageClient
from models.clip_classification import ClipClassification, ClipClassificationORM, CompositeClassification
from models.observation import ObservationORM
import utils.observations_sub_bucket as observations_sub_bucket


def get_rds_client() -> RdsStorageClient:
    """Create and connect an RDS storage client for clip classifications."""
    client = RdsStorageClient(base_orm=ClipClassificationORM)
    client.connect()
    return client


def read_clip_classification_from_s3(observer_id: str, observation_id: str) -> Optional[dict]:
    """Read a clip classification JSON file from S3.
    
    Args:
        observer_id: The observer UUID
        observation_id: The observation UUID
        
    Returns:
        The parsed JSON data or None if the file doesn't exist
    """
    path = f"{observer_id}/clip_classifications/{observation_id}.json"
    return observations_sub_bucket.read_json_file(path)


def parse_composite_classifications(data: dict) -> List[CompositeClassification]:
    """Parse composite classification data from the S3 JSON.
    
    Args:
        data: The parsed JSON data from S3
        
    Returns:
        List of CompositeClassification objects
    """
    composite_data = data.get('composite_classification', [])
    classifications = []
    
    for item in composite_data:
        classification = CompositeClassification(
            ranking=item.get('ranking', 0),
            label=item.get('label', ''),
            score_normalized=item.get('score_normalized', 0.0)
        )
        classifications.append(classification)
    
    return classifications


def store_classifications(
    observation_id: str, 
    classifications: List[CompositeClassification],
    rds_client: RdsStorageClient,
    current_time: int
) -> int:
    """Store clip classifications in RDS.
    
    Args:
        observation_id: The observation UUID
        classifications: List of CompositeClassification objects
        rds_client: The RDS storage client
        current_time: Current timestamp for created_at/updated_at
        
    Returns:
        Number of classifications stored
    """
    classification_orms = []
    
    for classification in classifications:
        orm = ClipClassificationORM(
            id=str(uuid4()),
            observation_id=observation_id,
            label=classification.label,
            score=classification.score_normalized,
            created_at=current_time,
            updated_at=current_time
        )
        classification_orms.append(orm)
    
    with rds_client.session_maker() as session:
        session.add_all(classification_orms)
        session.commit()
    
    return len(classification_orms)


def delete_existing_classifications(observation_id: str, rds_client: RdsStorageClient) -> int:
    """Delete existing classifications for an observation.
    
    Args:
        observation_id: The observation UUID
        rds_client: The RDS storage client
        
    Returns:
        Number of classifications deleted
    """
    with rds_client.session_maker() as session:
        deleted = session.query(ClipClassificationORM).filter_by(
            observation_id=observation_id
        ).delete()
        session.commit()
        return deleted


def process_single_ad(observer_id: str, timestamp: str, observation_id: str) -> bool:
    """Process the clip classification for a single observation.
    
    This will allow for processing of individual observations as needed 
    (e.g., backfilling missing data, or processing new observations as they come in).
    
    Args:
        observer_id: The observer UUID
        timestamp: The observation timestamp (unused, kept for interface consistency)
        observation_id: The observation UUID
        
    Returns:
        True if classification was processed successfully, False otherwise
    """
    rds_client = get_rds_client()
    
    try:
        # Read classification data from S3
        data = read_clip_classification_from_s3(observer_id, observation_id)
        if not data:
            print(f"No clip classification found for {observer_id}/{observation_id}")
            return False
        
        # Parse the composite classifications
        classifications = parse_composite_classifications(data)
        if not classifications:
            print(f"No composite classifications in file for {observer_id}/{observation_id}")
            return False
        
        # Delete existing classifications for this observation (for idempotency)
        delete_existing_classifications(observation_id, rds_client)
        
        # Store the new classifications
        current_time = int(time.time() * 1000)  # Milliseconds since epoch
        count = store_classifications(observation_id, classifications, rds_client, current_time)
        
        print(f"Stored {count} classifications for observation {observation_id}")
        return True
        
    except Exception as e:
        print(f"Error processing {observer_id}/{observation_id}: {e}")
        return False
    finally:
        rds_client.disconnect()


def list_observations_from_rds() -> List[tuple]:
    """List all observations from RDS.
    
    Returns:
        List of tuples (observer_id, observation_id)
    """
    client = RdsStorageClient(base_orm=ObservationORM)
    client.connect()
    
    try:
        with client.session_maker() as session:
            observations = session.query(ObservationORM).all()
            return [(obs.observer_id, obs.observation_id) for obs in observations]
    finally:
        client.disconnect()


def list_clip_classification_files_for_observer(observer_id: str) -> List[str]:
    """List all clip classification files for an observer.
    
    Args:
        observer_id: The observer UUID
        
    Returns:
        List of observation IDs that have clip classification files
    """
    path = f"{observer_id}/clip_classifications/"
    try:
        files = observations_sub_bucket.list_dir(path, list_all=True)
        # Extract observation IDs from file paths
        # Path format: {observer_id}/clip_classifications/{observation_id}.json
        observation_ids = []
        for file_path in files:
            if file_path.endswith('.json'):
                filename = file_path.split('/')[-1]
                observation_id = filename.replace('.json', '')
                observation_ids.append(observation_id)
        return observation_ids
    except Exception as e:
        print(f"Error listing clip classifications for {observer_id}: {e}")
        return []


def list_all_observers() -> List[str]:
    """List all observer IDs from S3.
    
    Returns:
        List of observer UUIDs
    """
    dirs = observations_sub_bucket.list_dir("", list_all=True)
    # Filter to only include directories (ending with /)
    # and extract the observer ID (first part of the path)
    observer_ids = set()
    for d in dirs:
        if d.endswith('/'):
            observer_id = d.rstrip('/').split('/')[0]
            # Basic validation that it looks like a UUID
            if len(observer_id) == 36 and observer_id.count('-') == 4:
                observer_ids.add(observer_id)
    return list(observer_ids)


def process_all_ads(clear_existing: bool = False) -> dict:
    """Process clip classifications for all observations.
    
    This should be run to import all existing clip classifications into RDS.
    
    Args:
        clear_existing: If True, clear all existing classifications before processing
        
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'observers_processed': 0,
        'observations_found': 0,
        'classifications_stored': 0,
        'errors': 0
    }
    
    rds_client = get_rds_client()
    
    try:
        # Optionally clear existing classifications
        if clear_existing:
            print("Clearing existing classifications...")
            with rds_client.session_maker() as session:
                deleted = session.query(ClipClassificationORM).delete()
                session.commit()
                print(f"Deleted {deleted} existing classifications")
        
        # Get all observers
        print("Listing all observers from S3...")
        observers = list_all_observers()
        print(f"Found {len(observers)} observers")
        
        # Process each observer
        for observer_id in tqdm(observers, desc="Processing observers"):
            stats['observers_processed'] += 1
            
            # List clip classification files for this observer
            observation_ids = list_clip_classification_files_for_observer(observer_id)
            
            for observation_id in observation_ids:
                stats['observations_found'] += 1
                
                try:
                    # Read classification data from S3
                    data = read_clip_classification_from_s3(observer_id, observation_id)
                    if not data:
                        continue
                    
                    # Parse the composite classifications
                    classifications = parse_composite_classifications(data)
                    if not classifications:
                        continue
                    
                    # Delete existing classifications for this observation (for idempotency)
                    delete_existing_classifications(observation_id, rds_client)
                    
                    # Store the new classifications
                    current_time = int(time.time() * 1000)
                    count = store_classifications(observation_id, classifications, rds_client, current_time)
                    stats['classifications_stored'] += count
                    
                except Exception as e:
                    print(f"Error processing {observer_id}/{observation_id}: {e}")
                    stats['errors'] += 1
        
        print("\n=== Processing Complete ===")
        print(f"Observers processed: {stats['observers_processed']}")
        print(f"Observations found: {stats['observations_found']}")
        print(f"Classifications stored: {stats['classifications_stored']}")
        print(f"Errors: {stats['errors']}")
        
        return stats
        
    finally:
        rds_client.disconnect()


if __name__ == "__main__":
    """
    Usage:
    python -m utils.etl.clip_classification [--clear] [--observer-id OBSERVER_ID] [--observation-id OBSERVATION_ID]
    
    Options:
    --clear                             Clear existing classifications before processing all observations
    --observer-id OBSERVER_ID           Process only a specific observer. When provided, processes all observations for that observer.
    --observation-id OBSERVATION_ID     Process only a specific observation (requires --observer-id)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process clip classifications from S3 to RDS")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear existing classifications before processing"
    )
    parser.add_argument(
        "--observer-id",
        type=str,
        help="Process only a specific observer"
    )
    parser.add_argument(
        "--observation-id",
        type=str,
        help="Process only a specific observation (requires --observer-id)"
    )
    
    args = parser.parse_args()
    
    if args.observation_id:
        if not args.observer_id:
            print("Error: --observation-id requires --observer-id")
            exit(1)
        # Process single observation
        success = process_single_ad(args.observer_id, "", args.observation_id)
        exit(0 if success else 1)
    elif args.observer_id:
        # Process all observations for a specific observer
        rds_client = get_rds_client()
        try:
            observation_ids = list_clip_classification_files_for_observer(args.observer_id)
            print(f"Found {len(observation_ids)} clip classification files for observer {args.observer_id}")
            
            for observation_id in tqdm(observation_ids, desc="Processing observations"):
                try:
                    data = read_clip_classification_from_s3(args.observer_id, observation_id)
                    if not data:
                        continue
                    classifications = parse_composite_classifications(data)
                    if not classifications:
                        continue
                    delete_existing_classifications(observation_id, rds_client)
                    current_time = int(time.time() * 1000)
                    store_classifications(observation_id, classifications, rds_client, current_time)
                except Exception as e:
                    print(f"Error processing {observation_id}: {e}")
        finally:
            rds_client.disconnect()
    else:
        # Process all observations
        process_all_ads(clear_existing=args.clear)