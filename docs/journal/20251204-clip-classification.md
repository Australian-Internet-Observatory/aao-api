---
created: 2025-12-04
updated: 2025-12-04
author: Dan Tran
updated_by: Dan Tran
---

# Bringing Ad Classification to the AAO Dashboard

This document defines the scope of work required to bring ad classification and enrichment data to the Australian Ad Observatory (AAO) dashboard.

> **TL;DR**
>
> This task will enable the AAO dashboard to display automated ad classification data, allowing users to see categories assigned to ads (e.g., "Alcohol", "Gambling") along with confidence scores. A new filter will also be added to allow users to filter ads based on these classifications.
>
> This will take approximately 16 hours of development time, broken down into three main components: data ingestion (8 hours), batch processing API extension (3 hours), and frontend integration (5 hours).
>
> Expected delivery by COB December 11, 2025.

## Background

On November 20, Khanh announced that "Classification and enrichment available only via data download", and Dan Tran to make it visible on the dashboard. This should be Dan's highest priority when he returns from leave on December 3.

The classification data acts as a form of automated-tagging of ads instead of relying on manual tagging by users, so each individual ad can be assigned a category like "Alcohol", "Education and Careers", "Gambling", etc. Each ad can have multiple categories assigned to it, along with a confidence score for each category.

### Data Source and Format

The data is currently available in the `fta-mobile-observations-v2` S3 bucket, and are only available for participants in the 2025 Alcohol Study. The data is stored in JSON files under the following path format: `s3://fta-mobile-observations-v2/{observer_uuid}/clip_classifications/{observation_uuid}.json`.

For example, `s3://fta-mobile-observations-v2/9ffd17f8-90a3-4546-9466-d5f51471f59a/clip_classifications/013ba102-6a9c-4eb4-85a0-34fe28d53089.json` contains:

```json
{
   "classified_at": 1762013057,
   "elapsed_time": 0.4974246025085449,
   "candidates": [
      {
         "img_path": {
            "key": "9ffd17f8-90a3-4546-9466-d5f51471f59a/temp-v2/65c17c17-214f-46a9-ab6b-c50d2ffbadba/230.jpg",
            "bucket": "fta-mobile-observations-v2"
         },
         "text_raw": "bytomwalker",
         "source": "observation",
         "status": "SUCCESS",
         "content": {
            "elapsed_time": 0.2965829372406006,
            "classification": [
               {
                  "ranking": 0,
                  "label": "Gambling",
                  "score": 0.443
               },
               {
                  "ranking": 1,
                  "label": "Clothing and Accessories",
                  "score": 0.417
               },
               {
                  "ranking": 2,
                  "label": "Culture and Fine Arts",
                  "score": 0.391
               },
               {
                  "ranking": 3,
                  "label": "Alcohol",
                  "score": 0.391
               },
               {
                  "ranking": 4,
                  "label": "Gifts and Holiday Items",
                  "score": 0.39
               }
            ]
         }
      }
   ],
   "composite_classification": [
      {
         "ranking": 0,
         "label": "Gambling",
         "score_normalized": 0.443
      },
      {
         "ranking": 1,
         "label": "Clothing and Accessories",
         "score_normalized": 0.417
      },
      {
         "ranking": 2,
         "label": "Culture and Fine Arts",
         "score_normalized": 0.391
      },
      {
         "ranking": 3,
         "label": "Alcohol",
         "score_normalized": 0.391
      },
      {
         "ranking": 4,
         "label": "Gifts and Holiday Items",
         "score_normalized": 0.39
      }
   ]
}
```

Which can be generalised into the following data model:

```python
from typing import List


class Classification:
  ranking: int
  label: str
  score: float

  def __init__(self, ranking: int, label: str, score: float) -> None:
    self.ranking = ranking
    self.label = label
    self.score = score


class Content:
  elapsed_time: float
  classification: List[Classification]

  def __init__(self, elapsed_time: float, classification: List[Classification]) -> None:
    self.elapsed_time = elapsed_time
    self.classification = classification


class ImgPath:
  key: str
  bucket: str

  def __init__(self, key: str, bucket: str) -> None:
    self.key = key
    self.bucket = bucket


class Candidate:
  img_path: ImgPath
  text_raw: str
  source: str
  status: str
  content: Content

  def __init__(self, img_path: ImgPath, text_raw: str, source: str, status: str, content: Content) -> None:
    self.img_path = img_path
    self.text_raw = text_raw
    self.source = source
    self.status = status
    self.content = content


class CompositeClassification:
  ranking: int
  label: str
  score_normalized: float

  def __init__(self, ranking: int, label: str, score_normalized: float) -> None:
    self.ranking = ranking
    self.label = label
    self.score_normalized = score_normalized


class ClipClassification:
  classified_at: int
  elapsed_time: float
  candidates: List[Candidate]
  composite_classification: List[CompositeClassification]

  def __init__(self, classified_at: int, elapsed_time: float, candidates: List[Candidate], composite_classification: List[CompositeClassification]) -> None:
    self.classified_at = classified_at
    self.elapsed_time = elapsed_time
    self.candidates = candidates
    self.composite_classification = composite_classification
```

The main field of interest for the AAO dashboard is the `composite_classification` field, which provides an overall classification for the ad clip. Each entry in this list contains a `label` (the category assigned to the ad) and a `score_normalized` (the confidence score for that category).

## Work Breakdown

### Data Ingestion

Estimate: 8 hours

Develop a process to ingest the clip classification JSON files from the S3 bucket into the AAO dashboard's backend system. This will likely involve setting up an ETL (Extract, Transform, Load) pipeline to read the JSON files, parse them, and store the relevant data in a relational database for efficient querying. This includes:

- Setting up a trigger or scheduler to periodically check for new classification files in the S3 bucket.
- Parsing the JSON files to extract the `observer_uuid`, `observation_uuid`, and `composite_classification` data.
- Perform a database schema update to accommodate the new classification data, including creating new tables or modifying existing ones as necessary.
- Implementing data validation and error handling to ensure the integrity of the ingested data.
- Testing the ingestion process to ensure it works correctly and efficiently.

> Why is this needed?
>
> While we can read the JSON files directly from S3 on-demand, this approach would be inefficient and slow, especially as the volume of data grows. For example, reading a single JSON file from S3 takes around 30ms, and with, say, 20,000 ads, the total time to read all files would be around 10 minutes. By ingesting the data into a relational database, we can take advantage of indexing and optimized query performance, allowing for much faster retrieval of classification data when needed.

Tasks:

- [x] Design the database schema for storing ad classification data. This should include a new table called `ad_classifications` with the following fields:
  - `id`: Primary key
  - `observation_id`: Foreign key referencing the ad
  - `label`: The classification label (e.g., "Alcohol", "Gambling")
  - `score`: The confidence score for the classification
  - `created_at`: Timestamp of when the record was created
  - `updated_at`: Timestamp of when the record was last updated
- [x] Perform the database migration in the AAO backend to create the `ad_classifications` table using Alembic.
- [x] Implement the ETL pipeline to ingest classification data from S3 into the `ad_classifications` table. This include:
  - [x] Create a Python-based AWS lambda function to read JSON files from the specified S3 path.
  - [x] Parse the JSON files to extract relevant classification data.
  - [x] Insert the parsed data into the `ad_classifications` table in the RDS database.
  - [x] Create a trigger to run the Lambda function when new files are added to the S3 bucket.

Required environmental variables and configurations:
- `S3_BUCKET_NAME`: The name of the S3 bucket containing the classification files.
- `RDS_DATABASE_URL`: The connection string for the RDS database.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: Credentials for accessing AWS services.
- `LAMBDA_FUNCTION_NAME`: The name of the AWS Lambda function to be created.
- `LAMBDA_TRIGGER_S3_PATH`: The S3 path to monitor for new classification files.
- `LAMBDA_TIMEOUT`: The maximum execution time for the Lambda function.
- `LAMBDA_MEMORY_SIZE`: The amount of memory allocated to the Lambda function.
- `LOGGING_LEVEL`: The logging level for the Lambda function (e.g., DEBUG, INFO, ERROR).
- `RETRY_ATTEMPTS`: The number of retry attempts for failed S3 reads or database inserts.

### Batch Processing API

Estimate: 3 hours

Extend the existing AAO dashboard backend API to include endpoints for retrieving ad classification data. This will be achieved in a similar manner to tags and attributes (star, hidden), utilising the existing endpoint `POST /ads/batch/presign` to request presigned URLs for fetching classification data for multiple ads in a single request. This includes:

- Modifying the backend API to accept requests for ad classification data with a new metadata type, e.g., `classification`.
- Implementing the logic to fetch the relevant classification data from the database based on the requested ad IDs.
- Attaching the classification data to the response payload in a similar format to existing metadata types.
- Testing the API changes to ensure they work correctly and efficiently.

> Why is this needed?
>
> The existing batch processing API is designed to efficiently handle requests for multiple ads in a single call, reducing the number of network round-trips and improving performance. By extending this API to include classification data, we can leverage the existing infrastructure and patterns, ensuring consistency and efficiency in how metadata is retrieved for ads.

Tasks:

- [x] Update the `POST /ads/batch/presign` endpoint to handle requests for ad classification data.
- [x] Implement the logic to query the `ad_classifications` table for the requested ad IDs and retrieve the associated classification labels and scores.
- [x] Format the retrieved classification data and include it in the API response payload.