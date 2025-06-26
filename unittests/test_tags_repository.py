import unittest
from db.clients.rds_storage_client import RdsStorageClient
from db.repository import Repository
from models.tag import Tag, TagORM

tags_repository = Repository(
    model=Tag,
    client=RdsStorageClient(
        base_orm=TagORM
    )
)

class TagsRepositoryTestCase(unittest.TestCase):
    def test_create_tag(self):
        tag = Tag(
            id="test_id_create",
            name="Test Tag",
            description="This is a test tag.",
            hex="#FFFFFF"
        )
        tags_repository.create(tag)
        retrieved_tag = tags_repository.get({ "id": "test_id_create" })
        self.assertIsNotNone(retrieved_tag)
        self.assertEqual(retrieved_tag.id, tag.id)
        self.assertEqual(retrieved_tag.name, tag.name)
        self.assertEqual(retrieved_tag.description, tag.description)
        self.assertEqual(retrieved_tag.hex, tag.hex)
        # Delete the tag after test
        tags_repository.delete(tag)
        
    def test_list_tags(self):
        tags = [
            Tag(
                id=f"test_id_list_{i}",
                name=f"Test Tag {i}",
                description=f"This is a test tag {i}.",
                hex="#FFFFFF"
            ) for i in range(5)
        ]
        for tag in tags:
            tags_repository.create(tag)
        retrieved_tags = tags_repository.list()
        # self.assertEqual(len(retrieved_tags), len(tags))
        assert len(retrieved_tags) >= len(tags), "Number of retrieved tags does not match the number of created tags."
        for tag in tags:
            assert any(t.id == tag.id for t in retrieved_tags), f"Tag with id {tag.id} not found in retrieved tags."
            assert any(t.name == tag.name for t in retrieved_tags), f"Tag with name {tag.name} not found in retrieved tags."
            assert any(t.description == tag.description for t in retrieved_tags), f"Tag with description {tag.description} not found in retrieved tags."
            assert any(t.hex == tag.hex for t in retrieved_tags), f"Tag with hex {tag.hex} not found in retrieved tags."
        # Clean up after test
        for tag in tags:
            tags_repository.delete(tag)
            
    def test_delete_tag(self):
        tag = Tag(
            id="test_id_delete",
            name="Test Tag",
            description="This is a test tag.",
            hex="#FFFFFF"
        )
        tags_repository.create(tag)
        tags_repository.delete(tag)
        retrieved_tag = tags_repository.get({ "id": "test_id_delete" })
        self.assertIsNone(retrieved_tag)
        # Ensure the tag is deleted
        all_tags = tags_repository.list()
        self.assertNotIn(tag, all_tags)
    
if __name__ == '__main__':
    unittest.main()