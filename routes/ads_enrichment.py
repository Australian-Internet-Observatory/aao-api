from db.clients.rds_storage_client import RdsStorageClient
from db.shared_repositories import tags_repository, applied_tags_repository
from middlewares.authenticate import authenticate
from models.clip_classification import ClipClassificationORM
from routes import route
from utils import Response, use

@route('ads/{observer_id}/{timestamp}.{ad_id}/enrichment/classifications', 'GET')
@use(authenticate)
def get_ads_classification(event, response: Response):
    """Retrieve both automatic and manual classifications for an ad.
    
    Returns automatic classifications from CLIP model and manual classifications
    from user-applied tags.
    ---
    tags:
      - ads/enrichment
    responses:
      200:
        description: A successful response
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: True
                classifications:
                  type: object
                  properties:
                    automatic:
                      type: array
                      items:
                        type: object
                        properties:
                          label:
                            type: string
                          score:
                            type: number
                    manual:
                      type: array
                      items:
                        type: object
                        properties:
                          label:
                            type: string
      400:
        description: A failed response
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: False
                comment:
                  type: string
    """
    ad_id = event['pathParameters']['ad_id']
    
    try:
        # Get automatic classifications (CLIP)
        automatic_classifications = []
        rds_client = RdsStorageClient(base_orm=ClipClassificationORM)
        rds_client.connect()
        
        try:
            with rds_client.session_maker() as session:
                clip_results = session.query(ClipClassificationORM).filter(
                    ClipClassificationORM.observation_id == ad_id
                ).all()
                
                automatic_classifications = [
                    {
                        'label': result.label,
                        'score': result.score
                    }
                    for result in clip_results
                ]
                
                # Sort by score descending
                automatic_classifications.sort(key=lambda x: x['score'], reverse=True)
        finally:
            rds_client.disconnect()
        
        # Get manual classifications (tags)
        manual_classifications = []
        with applied_tags_repository.create_session() as applied_tags_session:
            ad_tags = applied_tags_session.get({'observation_id': ad_id})
            
            if ad_tags:
                tag_ids = [ad_tag.tag_id for ad_tag in ad_tags]
                
                # Get tag details
                with tags_repository.create_session() as tags_session:
                    for tag_id in tag_ids:
                        tag = tags_session.get_first({'id': tag_id})
                        if tag:
                            manual_classifications.append({
                                'label': tag.name
                            })
        
        return {
            'automatic': automatic_classifications,
            'manual': manual_classifications
        }
        
    except Exception as e:
        print(f"Error retrieving classifications for ad {ad_id}: {e}")
        return response.status(400).json({
            'comment': 'ERROR_RETRIEVING_CLASSIFICATIONS',
            'error': str(e)
        })