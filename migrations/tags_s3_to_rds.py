# Migrate the tag definitions from S3 to RDS (not to be confused with ad tags,
# which are the applied tags to observations).

from tqdm import tqdm
from db.clients.rds_storage_client import RdsStorageClient
from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from models.tag import Tag, TagORM

s3_tags_repository = Repository(
    model=Tag,
    client=S3StorageClient(
        bucket='fta-mobile-observations-holding-bucket',
        prefix='metadata/tags',
        extension='json'
    )
)

rds_tags_repository = Repository(
    model=Tag,
    client=RdsStorageClient(
        base_orm=TagORM
    )
)

def main():
    # Move all tags from S3 to RDS
    print("Starting migration of tags from S3 to RDS...")
    s3_tags = s3_tags_repository.list()
    for tag in tqdm(s3_tags):
        try:
            rds_tags_repository.create_or_update(tag)
        except Exception as e:
            print(f"Failed to migrate tag {tag.id}: {e}")
    print("Migration completed.")
    
if __name__ == "__main__":
    main()