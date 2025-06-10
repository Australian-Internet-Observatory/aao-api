import unittest
from db.clients.s3_storage_client import S3StorageClient
from db.repository import Repository
from models.tag import Tag 

tags_repository = Repository(
    model=Tag,
    client=S3StorageClient(
        bucket='fta-mobile-observations-unit-test-bucket',
        prefix='metadata/tags',
        extension='json'
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
        retrieved_tag = tags_repository.get("test_id_create")
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
        self.assertEqual(len(retrieved_tags), len(tags))
        for i, tag in enumerate(tags):
            self.assertEqual(retrieved_tags[i].id, tag.id)
            self.assertEqual(retrieved_tags[i].name, tag.name)
            self.assertEqual(retrieved_tags[i].description, tag.description)
            self.assertEqual(retrieved_tags[i].hex, tag.hex)
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
        retrieved_tag = tags_repository.get("test_id")
        self.assertIsNone(retrieved_tag)
        # Ensure the tag is deleted
        all_tags = tags_repository.list()
        self.assertNotIn(tag, all_tags)
    
if __name__ == '__main__':
    unittest.main()