
from observations_repository import Observer
from dataclasses import dataclass

@dataclass
class OcrTextMatch:
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float

@dataclass
class OcrDataKeyframe:
    screenshot_cropped: str
    y_offset: int
    observed_at: str
    ocr_data: list[OcrTextMatch]

class RdoBuilder:
    def __init__(self, observer: Observer):
        self.observer = observer

    def compute_ad_dimensions(self, timestamp, ad_id):
        """Computes the dimensions of the ad for a given timestamp and ad_id
        
        Args:
            timestamp (int): The timestamp of the observation
            ad_id (str): The ad_id of the observation
            
        Returns:
            dict: A dictionary containing the width and height of the ad
        """
        output_from_restitcher = self.observer.get_output_from_restitcher(timestamp, ad_id)
        ad_content = self.observer.get_ad_content(timestamp, ad_id)
        frames = output_from_restitcher['frames']
        
        height = max([frame.get("h", 0) for frame in frames])
        width = ad_content.get("nameValuePairs", {}).get("frameSampleMetadata", {}).get("nameValuePairs", {}).get("statistics", {}).get("nameValuePairs", {}).get("w", 0)
        
        return {
            "w": width,
            "h": height
        }

    def compute_ocr_data(self, timestamp, ad_id):
        """Computes OCR data for a given timestamp and ad_id

        Args:
            timestamp (int): The timestamp of the observation
            ad_id (str): The ad_id of the observation

        Returns:
            list[OcrDataKeyframe]: A list of OcrDataKeyframe objects containing the OCR matches for each keyframe, relative to the top of the re-stitched image
        """
        output_from_scrape = self.observer.get_output_from_scrape(timestamp, ad_id)
        output_from_restitcher = self.observer.get_output_from_restitcher(timestamp, ad_id)
        
        frames = output_from_restitcher['frames']
        raw_ocr_data = output_from_scrape['ocr_data']
        
        frame_ids = [frame['id'] for frame in frames]
        outputs = []
        for index, frame_id in enumerate(frame_ids):
            raw_ocr_data_key = f"{self.observer.observer_id}/temp/{timestamp}.{ad_id}/{frame_id}"
            frame_ocr_data = raw_ocr_data.get(raw_ocr_data_key, [])
            if not frame_ocr_data:
                continue
            restitcher_frame = frames[index]
            restitcher_offset = restitcher_frame.get('y_source', {})
            offset_top = restitcher_offset.get('t', 0)
            offset_bottom = restitcher_offset.get('b', 0)
            ocr_data_with_offset = []
            for text_match in frame_ocr_data:
                if text_match.get('y', 0) < offset_top:
                    continue
                if text_match.get('y', 0) > offset_bottom:
                    break
                text_match_with_offset = {
                    **text_match,
                    "y": text_match.get('y', 0) - offset_top
                }
                ocr_data_with_offset.append(text_match_with_offset)
            outputs.append({
                "screenshot_cropped": frame_id,
                "y_offset": restitcher_frame.get('y_composite', {}).get('t', 0) - restitcher_frame.get('y_source', {}).get('t', 0) - 2,
                "observed_at": timestamp, # TODO: Update later with actual timestamp
                "ocr_data": ocr_data_with_offset
            })
        return outputs
    
    
if __name__ == "__main__":
    observer_id = "f60b6e94-7625-4044-9153-1f70863f81d8"
    timestamp = "1729569092202"
    ad_id = "d14f1dc0-5685-49e5-83d9-c46e29139373"
    observer = Observer(observer_id)
    
    rdo_builder = RdoBuilder(observer)
    
    print(rdo_builder.compute_ad_dimensions(timestamp, ad_id))