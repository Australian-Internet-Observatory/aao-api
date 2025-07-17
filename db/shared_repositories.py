from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.ad_tag import AdTag, AdTagORM
from models.attribute import AdAttribute, AdAttributeORM
from models.tag import Tag, TagORM
from models.user import User, UserORM, UserIdentity, UserIdentityORM

users_repository = Repository(
    model=User,
    client=RdsStorageClient(
        base_orm=UserORM
    )
)

user_identities_repository = Repository(
    model=UserIdentity,
    keys=['user_id', 'provider'],
    auto_generate_key=False,
    client=RdsStorageClient(
        base_orm=UserIdentityORM
    )
)

ad_attributes_repository = Repository(
    model=AdAttribute,
    keys=['observation_id', 'key'],
    auto_generate_key=False,
    client=RdsStorageClient(
        base_orm=AdAttributeORM
    )
)

tags_repository = Repository(
    model=Tag,
    client=RdsStorageClient(
        base_orm=TagORM
    )
)

applied_tags_repository = Repository(
    model=AdTag,
    keys=['observation_id', 'tag_id'],
    client=RdsStorageClient(
        base_orm=AdTagORM
    )
)

