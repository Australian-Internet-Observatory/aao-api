"""
Integration tests for export endpoints.

These tests verify the export API functionality. Since the export worker
is a separate service, we mock the SQS client to verify that messages
are sent correctly without depending on an actual queue.
"""
import json
import sys
from utils.sqs_client import SQSClient

sys.path.append("../")

from base import execute_endpoint
from db.shared_repositories import (
    exports_repository,
    shared_exports_repository,
    users_repository
)


# Test data
SAMPLE_EXPORT_PARAMETERS = {
    "query": {
        "method": "AND",
        "args": [
            {
                "method": "DATETIME_AFTER",
                "args": ["1767276000000"]
            },
            {
                "method": "DATETIME_BEFORE",
                "args": ["1767967200000"]
            }
        ]
    },
    "include_images": False,
    "fields": [
        "observer.uuid",
        "observation.uuid"
    ]
}


def test_create_export_success():
    res = execute_endpoint(
        endpoint='/exports',
        method='POST',
        body={
            "query": {
                "method": "OBSERVATION_ID_CONTAINS",
                "args": ["b2c11dfe295b"]
            },
            "include_images": False,
            "fields": [
                "observer.uuid",
                "observation.uuid"
            ]
        },
        auth=True
    )
    assert res['statusCode'] == 201
    response_body = res['body']
    print(response_body)
    sqs_client = SQSClient()
    messages = sqs_client.poll_message(wait_time=2, max_messages=1)
    assert len(messages) == 1
    message_body = json.loads(messages[0]['Body'])
    print(">>> SQS Message Body:")
    print(message_body)
    assert message_body['export_id'] == response_body['export']['export_id']
    assert message_body['export_parameters']['query']['method'] == 'OBSERVATION_ID_CONTAINS'
    assert message_body['export_parameters']['query']['args'] == ['b2c11dfe295b']
    assert message_body['export_parameters']['include_images'] is False
    
    # Ensure export record exists
    export_id = response_body['export']['export_id']
    with exports_repository.create_session() as session:
        export_record = session.get_first({'id': export_id})
        print(">>> Export Record:")
        print(export_record)
        assert export_record is not None
        assert export_record.status == 'pending'
    
    # Cleanup
    sqs_client.delete_message(messages[0]['ReceiptHandle'])
    with exports_repository.create_session() as session:
        session.delete({'id': export_id})

def test_get_completed_export():
    """This test is not modular since it depends on an existing completed export in the DB.
    
    To run this test, ensure there is an export with status 'completed' and the specified ID, and this export must be completed by a runner with an actual file in object storage.
    
    This test may fail at a later date as exports are only stored for 7 days after completion. It is therefore commeted out by default.
    """
    pass
    # completed_export_id = "ac0dbe27-1946-4acb-b5e2-d8095306dd01"
    # res = execute_endpoint(
    #     endpoint=f'/exports/{completed_export_id}',
    #     method='GET',
    #     auth=True
    # )
    # assert res['statusCode'] == 200
    # response_body = res['body']
    # print(response_body)
    # assert response_body['export_id'] == completed_export_id
    # assert response_body['status'] == 'completed'


def test_share_export_success():
    # Create an export to share
    res = execute_endpoint(
        endpoint='/exports',
        method='POST',
        body={
            "query": {
                "method": "OBSERVATION_ID_CONTAINS",
                "args": ["b2c11dfe295b"]
            },
            "include_images": False,
            "fields": [
                "observer.uuid",
                "observation.uuid"
            ]
        },
        auth=True
    )
    assert res['statusCode'] == 201
    response_body = res['body']
    export_id = response_body['export']['export_id']

    # Create a target user to share with
    with users_repository.create_session() as session:
        target_user = session.create({
            'full_name': 'Share Target (Auto-generated)',
            'enabled': True,
            'role': 'user'
        })
        target_user_id = target_user['id']

    try:
        # Share the export
        share_res = execute_endpoint(
            endpoint=f'/exports/{export_id}/share',
            method='POST',
            body={
                'user_ids': [target_user_id]
            },
            auth=True
        )
        assert share_res['statusCode'] == 200
        share_body = share_res['body']
        assert share_body['success'] is True
        assert target_user_id in share_body['shared_with']

        # Verify the shared record exists in DB
        with shared_exports_repository.create_session() as s_session:
            shared_record = s_session.get_first({'export_id': export_id, 'user_id': target_user_id})
            assert shared_record is not None

    finally:
        # Cleanup: unshare, delete export, delete user
        execute_endpoint(
            endpoint=f'/exports/{export_id}/unshare',
            method='POST',
            body={'user_ids': [target_user_id]},
            auth=True
        )
        with exports_repository.create_session() as e_session:
            e_session.delete({'id': export_id})
        with users_repository.create_session() as u_session:
            u_session.delete({'id': target_user_id})


def test_delete_export_success():
    # Create an export to delete
    res = execute_endpoint(
        endpoint='/exports',
        method='POST',
        body={
            "query": {
                "method": "OBSERVATION_ID_CONTAINS",
                "args": ["b2c11dfe295b"]
            },
            "include_images": False,
            "fields": [
                "observer.uuid",
                "observation.uuid"
            ]
        },
        auth=True
    )
    assert res['statusCode'] == 201
    response_body = res['body']
    export_id = response_body['export']['export_id']

    # Delete the export
    del_res = execute_endpoint(
        endpoint=f'/exports/{export_id}',
        method='DELETE',
        auth=True
    )
    assert del_res['statusCode'] == 200
    del_body = del_res['body']
    assert del_body['success'] is True

    # Ensure export no longer exists
    with exports_repository.create_session() as session:
        export_record = session.get_first({'id': export_id})
        assert export_record is None
    