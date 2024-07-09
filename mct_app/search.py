from typing import Any

from flask import current_app

"""
These are the main functions for manipulating Elasticsearch.
You can do a full-text search.
"""


def add_to_index(index: int, model: Any) -> None:
    """Add a new index to Elasticsearch."""
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)


def remove_from_index(index: int, model: Any) -> None:
    """Remove a chosen index from Elasticsearch."""
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index: int,
                query,
                page: int,
                per_page: int) -> tuple[int, dict[str, str]]:
    """Add query for chosen index."""
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page
    )
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
