# Migrate the tag definitions from S3 to RDS (not to be confused with ad tags,
# which are the applied tags to observations).

from tqdm import tqdm
from db.clients.rds_storage_client import RdsStorageClient
from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from models.ad_tag import LegacyAdTag, AdTag, AdTagORM
from db.shared_repositories import applied_tags_repository as rds_ads_tags_repository

s3_ads_tags_repository = Repository(
    model=LegacyAdTag,
    keys=['id'],
    client=S3StorageClient(
        bucket='fta-mobile-observations-holding-bucket',
        prefix='metadata/ads_tags',
        extension='json',
        keys=['id']
    )
)

def main():
    # Move all ad tags from S3 to RDS
    print("Starting migration of ad tags from S3 to RDS...")
    s3_ads_tags = s3_ads_tags_repository.list()
    print(f"Found {len(s3_ads_tags)} ad tags in S3. Starting migration...")
        
    with rds_ads_tags_repository.create_session() as session:
        for ad_tag in tqdm(s3_ads_tags):
            try:
                # Convert LegacyAdTag to AdTag
                observation_id = ad_tag.id.split('.')[-1]
                tags = ad_tag.tags
                for tag_id in tags:
                    ad_tag_data = AdTag(
                        observation_id=observation_id,
                        tag_id=tag_id
                    )
                    session.create_or_update(ad_tag_data)
            except Exception as e:
                print(f"Failed to migrate ad tag {ad_tag.id}: {e}")
                
    print("Migration completed.")
    
if __name__ == "__main__":
    main()