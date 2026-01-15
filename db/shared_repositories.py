from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.ad_tag import AdTag, AdTagORM
from models.attribute import AdAttribute, AdAttributeORM
from models.observation import Observation, ObservationORM
from models.tag import Tag, TagORM
from models.user import User, UserORM, UserIdentity, UserIdentityORM
from models.export import (
    Export, ExportORM, 
    SharedExport, SharedExportORM, 
    ExportableField, ExportableFieldORM,
    ExportField, ExportFieldORM
)

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

observations_repository = Repository(
    model=Observation,
    keys=['observation_id'],
    auto_generate_key=False,
    client=RdsStorageClient(
        base_orm=ObservationORM
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

# Export-related repositories
exports_repository = Repository(
    model=Export,
    client=RdsStorageClient(
        base_orm=ExportORM
    )
)

shared_exports_repository = Repository(
    model=SharedExport,
    keys=['export_id', 'user_id'],
    auto_generate_key=False,
    client=RdsStorageClient(
        base_orm=SharedExportORM
    )
)

exportable_fields_repository = Repository(
    model=ExportableField,
    client=RdsStorageClient(
        base_orm=ExportableFieldORM
    )
)

export_fields_repository = Repository(
    model=ExportField,
    keys=['export_id', 'field_id'],
    auto_generate_key=False,
    client=RdsStorageClient(
        base_orm=ExportFieldORM
    )
)
