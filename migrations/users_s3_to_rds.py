import json
from uuid import uuid4

from tqdm import tqdm
from models.user import User
import utils.metadata_sub_bucket as metadata

from db.shared_repositories import users_repository

USERS_FOLDER_PREFIX = 'dashboard-users'


def list_users_credential_file_paths():
    return [path.replace(f"{USERS_FOLDER_PREFIX}/", "") for path in metadata.list_objects(f"{USERS_FOLDER_PREFIX}/") if path.endswith('credentials.json')]

def list_users_token_file_paths():
    return [path.replace(f"{USERS_FOLDER_PREFIX}/", "") for path in metadata.list_objects(f"{USERS_FOLDER_PREFIX}/") if 'sessions' in path]

class UserEntities:
    def __init__(self):
        self.credential_paths = list_users_credential_file_paths()
        self.token_paths = list_users_token_file_paths()
    
    def list_usernames(self):
        print(self.credential_paths)
        return [path.split('/')[0] for path in self.credential_paths]
    
    def get_entity(self, username: str) -> dict:
        credential_path = f"{USERS_FOLDER_PREFIX}/{username}/credentials.json"
        token_path = next((path for path in self.token_paths if username in path), None)
        if token_path:
            token_path = token_path.replace(f"{username}/sessions/", "")
        
        credentials = json.loads(metadata.get_object(credential_path, read_body=True))
        
        return {
            "username": credentials['username'],
            "password": credentials['password'],
            "full_name": credentials.get('full_name', ''),
            "enabled": credentials.get('enabled', True),
            "role": credentials.get('role', 'user'),  # Default to 'user' if not specified
            "current_token": token_path if token_path else None
        }

def main():
    user_entities = UserEntities()
    usernames = user_entities.list_usernames()
    
    for username in tqdm(usernames):
        user = user_entities.get_entity(username)
        user_entity = User(
            id=str(uuid4()),  # Generate a new UUID for the user ID
            **user,
        )
        try:
            with users_repository.create_session() as session:
                session.create(user_entity)
        except Exception as e:
            if 'duplicate key value violates unique constraint' in str(e):
                continue
            print(f"Error creating user {username}: {e}")
            continue
    
    print("Migration completed successfully.")
    
if __name__ == "__main__":
    main()