"""Generated API schemas must identify every method without ambiguous operation IDs."""
import warnings
from nsai.api import app


def test_operation_ids_are_unique_for_all_methods():
    previous=app.openapi_schema
    app.openapi_schema=None
    try:
        with warnings.catch_warnings(record=True) as recorded:
            schema=app.openapi()
        identities=[operation['operationId'] for item in schema['paths'].values() for method,operation in item.items() if method in {'get','head','post','put','patch','delete','options'}]
        assert len(identities)==len(set(identities))
        assert not any('Duplicate Operation ID' in str(w.message) for w in recorded)
        original=schema['paths']['/v1/sources/{document_id}/original']
        assert original['get']['operationId']!=original['head']['operationId']
    finally:
        app.openapi_schema=previous
