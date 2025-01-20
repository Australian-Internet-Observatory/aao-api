import boto3
import os
import json

from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

session_sydney = boto3.Session(
    region_name='ap-southeast-2',
    aws_access_key_id=config['AWS']['ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS']['SECRET_ACCESS_KEY']
)

MOBILE_OBSERVATIONS_BUCKET = 'fta-mobile-observations-v2'

client = session_sydney.client('s3')

def list_dir(path=""):
    # If the path does not have an extension, it is a directory
    if not os.path.splitext(path)[1] and not path.endswith('/'):
        path += '/'
    # for obj in observation_bucket.objects.filter(Prefix=path, Delimiter='/'):
    #     print(obj.key)
    kwargs = {
        'Bucket': MOBILE_OBSERVATIONS_BUCKET, 
        'Delimiter': '/'
    }
    if path and path not in ["/", "", ".", "./"]:
        kwargs['Prefix'] = path
    client_response = client.list_objects_v2(**kwargs)
    dir_elements = []
    for content in client_response.get('CommonPrefixes', []):
        dir_name = content.get('Prefix')
        dir_elements.append(dir_name)
    for content in client_response.get('Contents', []):
        file_name = content.get('Key')
        dir_elements.append(file_name)
    return dir_elements

def read_json_file(path):
    try:
        obj = client.get_object(Bucket=MOBILE_OBSERVATIONS_BUCKET, Key=path)
        data = obj['Body'].read().decode('utf-8')
        return json.loads(data)
    except Exception as e:
        print('Error reading file:', path)
        print(e)
        return None
    
def try_get_object(key, bucket=MOBILE_OBSERVATIONS_BUCKET):
    try:
        return client.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        return None


class Observer:
    def __init__(self, observer_id):
        self.observer_id = observer_id
        # self.expected_subdirs = [
        #     'display',
        #     'meta_adlibrary_scrape',
        #     'misc',
        #     'rdo',
        #     'relation',
        #     'stitching',
        #     'temp'
        # ]
        
    def read_json_file(self, path):
        return read_json_file(f"{self.observer_id}/{path}")
    
    def get_output_from_scrape(self, timestamp, ad_id):
        prefix = f"{self.observer_id}/meta_adlibrary_scrape/{timestamp}.{ad_id}"
        filename = "output_from_scrape.json"
        return read_json_file(f"{prefix}/{filename}")
        
    def get_output_from_restitcher(self, timestamp, ad_id):
        prefix = f"{self.observer_id}/stitching/{timestamp}.{ad_id}"
        filename = "output_from_restitcher.json"
        return read_json_file(f"{prefix}/{filename}")
    
    def get_relation_outputs(self, timestamp, ad_id):
        prefix = f"{self.observer_id}/relation/{timestamp}.{ad_id}"
        modes = {
            "ocr": "output.json",
            "images": "images_comparison.json",
            "videos": "videos_comparison.json"
        }
        outputs = {}
        for mode, filename in modes.items():
            outputs[mode] = read_json_file(f"{prefix}/{filename}")
        return outputs

    def get_ad_content(self, timestamp, ad_id):
        prefix = f"{self.observer_id}/temp/{timestamp}.{ad_id}"
        filename = "adContent.json"
        return read_json_file(f"{prefix}/{filename}")

# class Observation:
#     def __init__(self, observer_id, timestamp, ad_id):
#         self.observer_id = observer_id
#         self.timestamp = timestamp
#         self.ad_id = ad_id
        
#     def read_json_file(self, category, path):
#         prefix = f"{self.observer_id}/{category}/{self.timestamp}.{self.ad_id}"
#         return read_json_file(f"{prefix}/{path}")

if __name__ == "__main__":
    # observer_id = "f60b6e94-7625-4044-9153-1f70863f81d8"
    # timestamp = "1729569092202"
    # ad_id = "d14f1dc0-5685-49e5-83d9-c46e29139373"
    # observer = Observer(observer_id)
    pass
    