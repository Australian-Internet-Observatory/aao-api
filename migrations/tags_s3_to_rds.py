# Migrate the tag definitions from S3 to RDS (not to be confused with ad tags,
# which are the applied tags to observations).

from tqdm import tqdm
from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from models.tag import Tag
from db.shared_repositories import tags_repository as rds_tags_repository

s3_tags_repository = Repository(
    model=Tag,
    client=S3StorageClient(
        bucket='fta-mobile-observations-holding-bucket',
        prefix='metadata/tags',
        extension='json'
    )
)

def main():
    # Move all tags from S3 to RDS
    print("Starting migration of tags from S3 to RDS...")
    s3_tags = s3_tags_repository.list()
    with rds_tags_repository.create_session() as session:
        for tag in tqdm(s3_tags):
            try:
                session.create_or_update(tag)
            except Exception as e:
                print(f"Failed to migrate tag {tag.id}: {e}")
    print("Migration completed.")
    
if __name__ == "__main__":
    main()