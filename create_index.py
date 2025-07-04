from routes.ads import parse_ad_path
from utils import observations_sub_bucket
from utils.indexer.registry import IndexRegistry
from utils.indexer.indexer import Indexer
from tqdm import tqdm
from datetime import datetime
import multiprocessing
import re

class Logger:
    """A simple logger class to save logs to a file."""
    def __init__(self, filename=None, verbose=False):
        self.filename = filename
        self.file = open(filename, 'a') if filename else None
        self.verbose = verbose
    
    def log(self, message):
        """Log a message to the file."""
        if self.verbose: print(message)
        if self.file is None:
            return
        self.file.write(f"{message}\n")
        
    def close(self):
        """Close the log file."""
        self.file.close()

logger = Logger(verbose=True)

def list_failed_ads(log_file_path):
    # Get all available ads
    available_ads = list_ads_to_index()
    ads_lookup = {ad['ad_id']: ad for ad in available_ads}
    
    failed_ads = []
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            if "Error indexing ad" not in line: continue
            regex = r"Error indexing ad (?P<ad_id>[\w-]+): (?P<error>.+)"
            match = re.search(regex, line)
            if not match: continue
            ad_id = match.group("ad_id")
            if ad_id not in ads_lookup: continue
            ad_info = ads_lookup[ad_id]
            failed_ads.append(ad_info)
            
    return failed_ads

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
    ads = list(set(data.get("ads_passed_rdo_construction", [])))
    
    # 2. Parse the ads to get the ad_id, timestamp, and observer_id
    ads_to_index = [parse_ad_path(ad) for ad in ads]
    
    return ads_to_index

def put_index(observer_id, timestamp, ad_id, skip_on_error=False):
    indexer = Indexer(stage='staging', skip_on_error=skip_on_error)
    indexer.put_index_open_search(observer_id, timestamp, ad_id)
    
def put_index_star(args):
    """Wrapper function to unpack arguments for multiprocessing."""
    return put_index(*args)

def index_list(ads, max_workers=50):
    """Index a list of ads."""
    # If 1 worker, do it sequentially
    if max_workers == 1:
        for ad in tqdm(ads, desc="Indexing ads", unit="ad"):
            put_index(ad["observer_id"], ad["timestamp"], ad["ad_id"], skip_on_error=True)
        return

    # Otherwise, use multiprocessing
    print(f"Using {max_workers} workers to index ads")
    with multiprocessing.Pool(processes=max_workers) as pool:
        # Create a list of arguments for each ad
        args = [(ad["observer_id"], ad["timestamp"], ad["ad_id"], True) for ad in ads]
        
        # Use tqdm to show progress
        for _ in tqdm(
                pool.imap_unordered(put_index_star, args), 
                total=len(args), 
                desc="Indexing ads", 
                unit="ad"
            ):
            pass

def index_all_ads():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger = Logger(f"ads_indexing_{timestamp}.log", verbose=True)
    logger.log("Starting the indexing process")
    
    # Get the list of ads to be indexed
    ads_to_index = list_ads_to_index()
    assert len(ads_to_index) > 0, "No ads to index"
    logger.log(f"Found {len(ads_to_index)} ads to index")
    
    # Put the ads in the index
    index_list(ads_to_index)
        
    logger.log("Indexing process completed")
    logger.close()

def index_failed_ads(log_file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logger = Logger(f"ads_indexing_failed_{timestamp}.log", verbose=True)
    logger.log("Starting the indexing of failed ads")
    # Get the list of failed ads from the log file
    failed_ads = list_failed_ads(log_file_path)
    assert len(failed_ads) > 0, "No failed ads to index"
    logger.log(f"Found {len(failed_ads)} failed ads to index")
    
    # Put the failed ads in the index
    index_list(failed_ads)
    
    logger.log("Indexing of failed ads completed")
    logger.close()


if __name__ == "__main__":
    registry = IndexRegistry()
    registry.prepare(prefix='reduced-rdo-index_')
    registry.start()
    
    try:
        index_all_ads()
    except Exception as e:
        print(f"Error during indexing: {e}")
        registry.fail()
        exit(1)
    
    registry.complete()
    
    latest_index = registry.get_latest()
    print(f"Completed indexing: {latest_index.name}")