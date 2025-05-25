from routes.ads import parse_ad_path
from utils import observations_sub_bucket
from utils.opensearch.rdo_open_search import AdWithRDO, RdoOpenSearch
from tqdm import tqdm
from datetime import datetime

class Logger:
    """A simple logger class to save logs to a file."""
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'a')
    
    def log(self, message):
        """Log a message to the file."""
        print(message)
        self.file.write(f"{message}\n")
        
    def close(self):
        """Close the log file."""
        self.file.close()

logger = None

def list_ads_to_index():
    # This function should return a list of dictionaries with ad_id, timestamp, and observer_id
    # For example:
    # return [
    #     # {"ad_id": "6e49c7a8-df11-4f5d-8696-d48498ebee64", "timestamp": "1743664069050", "observer_id": "447745c4-2cbc-4c7b-872e-454d953ce65a"},
    #     {"ad_id": "545ba836-81fe-4861-bc2e-6c8bfbe4e587", "timestamp": "1744851600298", "observer_id": "9e194bee-46ac-4fd9-ac6e-a11b4dcfc18c"},
    #     # Add more ads as needed
    # ]
    
    # 1. Read the ads from the ads_stream.json
    data = observations_sub_bucket.read_json_file("ads_stream.json")
    ads = data.get("ads_passed_rdo_construction", [])
    
    # 2. Parse the ads to get the ad_id, timestamp, and observer_id
    ads_to_index = [parse_ad_path(ad) for ad in ads]
    
    return ads_to_index


def put_index(observer_id, timestamp, ad_id, skip_on_error=False):
    ad_with_rdo = AdWithRDO(observer_id, timestamp, ad_id)
    open_search = RdoOpenSearch()
    data = ad_with_rdo.fetch_rdo()
    try:
        open_search.put(ad_with_rdo, data)
    except Exception as e:
        if skip_on_error:
            logger.log(f"Error indexing ad {ad_id}: {e}")
        else:
            raise e
    
if __name__ == "__main__":
    # put_index("447745c4-2cbc-4c7b-872e-454d953ce65a", "1743664069050", "6e49c7a8-df11-4f5d-8696-d48498ebee64")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger = Logger(f"ads_indexing_{timestamp}.log")
    logger.log("Starting the indexing process")
    
    # 1. Get the list of ads to be indexed as a list of dictionaries { ad_id, timestamp, observer_id }
    ads_to_index = list_ads_to_index()
    assert len(ads_to_index) > 0, "No ads to index"
    logger.log(f"Found {len(ads_to_index)} ads to index")
    
    # 2. Put the ads in the index
    for ad in tqdm(ads_to_index, desc="Indexing ads", unit="ad"):
        put_index(ad["observer_id"], ad["timestamp"], ad["ad_id"], skip_on_error=True)
        
    logger.log("Indexing process completed")
    logger.close()