from models.ad_tag import AdTag
import pandas as pd
from db.shared_repositories import applied_tags_repository

mock_old_applied_tags = [
    {
        "observation_id": "old_observation_id",
        "tag_id": "tag_1"
    },
    {
        "observation_id": "old_observation_id",
        "tag_id": "tag_2"
    },
    {
        "observation_id": "old_observation_id_1",
        "tag_id": "tag_1"
    },
    {
        "observation_id": "old_observation_id_1",
        "tag_id": "tag_2"
    },
    {
        "observation_id": "old_observation_id_1",
        "tag_id": "tag_3"
    },
    {
        "observation_id": "old_observation_id_2",
        "tag_id": "tag_2"
    },
    {
        "observation_id": "old_observation_id_2",
        "tag_id": "tag_4"
    },
    {
        "observation_id": "old_observation_id_3",
        "tag_id": "tag_2"
    },
    {
        "observation_id": "old_observation_id_4",
        "tag_id": "tag_1"
    },
    {
        "observation_id": "old_observation_id_4",
        "tag_id": "tag_2"
    },
    {
        "observation_id": "old_observation_id_5",
        "tag_id": "tag_1"
    }
]

observation_id_mappings = [
    # Case 1: A single old observation ID is mapped to multiple new observation IDs
    # so we copy the tags from the old observation ID to each of the new observation IDs.
    {
        "from": "old_observation_id",
        "to": "new_observation_id_1",
    },
    {
        "from": "old_observation_id",
        "to": "new_observation_id_2",
    },
    # Case 2: Two old observation IDs are mapped to a single new observation ID
    # so we copy the tags from both old observation IDs to the new observation ID.
    {
        "from": "old_observation_id_1",
        "to": "new_observation_id",
    },
    {
        "from": "old_observation_id_2",
        "to": "new_observation_id",
    },
    # Case 3: A single old observation ID is mapped to a single new observation ID
    # so we copy the tags from the old observation ID to the new observation ID.
    {
        "from": "old_observation_id_3",
        "to": "new_observation_id_3",
    },
    # Case 4: Some old observation IDs are not mapped to any new observation IDs
    # so they will be deleted (e.g., old_observation_id_4 and old_observation_id_5 from above example).
]



def main(commit: bool = False):
    applied_tags = mock_old_applied_tags
    # When migrating, replace with:
    # applied_tags = [entity.model_dump() for entity in applied_tags_repository.list()]
    
    # An inner join of the mapping and the applied tags will create a new DataFrame
    # where each old observation ID is mapped to its corresponding new observation IDs
    # along with the tags associated with the old observation IDs.
    # 
    # The join ensures the above cases are handled correctly:
    # - Case 1: One -> Many: Copy to each new observation ID.
    # - Case 2: Many -> One: Copy from all old observation IDs to the new observation ID.
    # - Case 3: One -> One: Copy from the old observation ID to the new observation ID.
    # - Case 4: No mapping: Not present in mapping so discarded.
    print("Creating mapping of old observation IDs to new observation IDs...")
    old_applied_tags_df = pd.DataFrame(applied_tags)
    print("Migrating from old observation IDs...")
    print(old_applied_tags_df)
    mapping_df = pd.DataFrame(observation_id_mappings)
    print("\nUsing the following mapping:")
    print(mapping_df)
    merged_df = mapping_df.merge(old_applied_tags_df, 
                                 left_on="from", 
                                 right_on="observation_id", 
                                 how='inner'
                                )
    
    # Ensure unique pairs of new observation IDs and tag IDs
    cleaned_df = merged_df[['to', 'tag_id']]\
        .rename(columns={'to': 'observation_id'})\
        .drop_duplicates(subset=['observation_id', 'tag_id'])
    
    print("\nCreated new applied tags DataFrame:")
    print(cleaned_df)
    
    if not commit:
        print("This is a dry run. No changes will be made to the repository.")
        return
    
    # Then, delete the old applied tags from the repository
    print("Deleting old applied tags from the repository...")
    for _, row in old_applied_tags_df.iterrows():
        old_applied_tag = AdTag(
            observation_id=row['observation_id'],
            tag_id=row['tag_id']
        )
        try:
            with applied_tags_repository.create_session() as session:
                session.delete(old_applied_tag)
        except ValueError as e:
            print(f"Error deleting applied tag {old_applied_tag}: {e}")
    
    # Finally, use the dataframe to create new applied tags in the repository
    print("Creating new applied tags in the repository...")
    for _, row in cleaned_df.iterrows():
        new_applied_tag = AdTag(
            observation_id=row['observation_id'],
            tag_id=row['tag_id']
        )
        try:
            with applied_tags_repository.create_session() as session:
                session.create(new_applied_tag)
        except ValueError as e:
            print(f"Error creating applied tag {new_applied_tag}: {e}")

    print("Migration completed successfully.")
    
if __name__ == "__main__":
    main(commit = False)