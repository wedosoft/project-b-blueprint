"""Utility script to bootstrap and validate the Qdrant collection used for embeddings.

Usage (from repository root):

```bash
python -m backend.infrastructure.embeddings.bootstrap_qdrant
```

Options include overriding the collection name or forcing recreation. Run with
`--help` for the full CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Tuple

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http import models as rest_models

from core.config import Settings, get_settings

DistanceAlias = rest_models.Distance


def build_client(settings: Settings) -> QdrantClient:
    """Instantiate a Qdrant client from application settings."""
    return QdrantClient(
        url=settings.qdrant.url,
        api_key=settings.qdrant.api_key.get_secret_value(),
        timeout=30,
    )


def ensure_collection(
    client: QdrantClient,
    collection: str,
    dimension: int,
    distance: DistanceAlias,
    force_recreate: bool = False,
) -> Tuple[bool, rest_models.CollectionInfo]:
    """Create the embeddings collection if it does not yet exist.

    Returns a tuple (created_or_recreated, collection_info).
    """
    if client.collection_exists(collection):
        info = client.get_collection(collection)
        existing_params = info.config.params.vectors
        if isinstance(existing_params, dict):
            existing_params = next(iter(existing_params.values()))

        existing_dim = getattr(existing_params, "size", None)
        existing_distance = getattr(existing_params, "distance", None)
        desired_distance_value = (
            distance.value if isinstance(distance, DistanceAlias) else str(distance).lower()
        )
        if isinstance(existing_distance, DistanceAlias):
            existing_distance_value = existing_distance.value
        elif existing_distance is None:
            existing_distance_value = None
        else:
            existing_distance_value = str(existing_distance).lower()

        if (
            existing_dim == dimension
            and existing_distance_value == desired_distance_value
        ):
            return False, info

        if not force_recreate:
            raise RuntimeError(
                f"Collection '{collection}' already exists with incompatible settings "
                f"(dimension={existing_dim}, distance={existing_distance}). "
                "Re-run with --force-recreate to rebuild."
            )

        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=rest_models.VectorParams(size=dimension, distance=distance),
        optimizers_config=rest_models.OptimizersConfigDiff(indexing_threshold=20_000),
        on_disk_payload=True,
        shard_number=1,
        replication_factor=1,
    )
    info = client.get_collection(collection)
    return True, info


def ensure_payload_indexes(client: QdrantClient, collection: str) -> None:
    """Create frequently-used payload indexes (idempotent)."""
    desired_indexes = {
        "organization_id": rest_models.PayloadSchemaType.KEYWORD,
        "knowledge_item_id": rest_models.PayloadSchemaType.KEYWORD,
        "tags": rest_models.PayloadSchemaType.KEYWORD,
        "embedding_model": rest_models.PayloadSchemaType.KEYWORD,
        "updated_at": rest_models.PayloadSchemaType.DATETIME,
    }

    for field_name, schema_type in desired_indexes.items():
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field_name,
                field_schema=schema_type,
            )
        except UnexpectedResponse as exc:
            if "already exists" in str(exc).lower():
                continue
            raise


def check_health(client: QdrantClient, collection: str) -> rest_models.CollectionStatus:
    """Return the health status for the specified collection."""
    info = client.get_collection(collection_name=collection)
    return info.status


def parse_args(default_collection: str, default_dimension: int) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap and validate the Qdrant collection used for embeddings."
    )
    parser.add_argument(
        "--collection",
        default=default_collection,
        help="Collection name to create or validate (default: %(default)s).",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=default_dimension,
        help="Vector dimension to enforce (default: %(default)s).",
    )
    parser.add_argument(
        "--distance",
        choices=["cosine", "dot", "euclid"],
        default="cosine",
        help="Vector distance metric (default: %(default)s).",
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Drop and recreate the collection when configuration mismatches.",
    )
    parser.add_argument(
        "--skip-indexes",
        action="store_true",
        help="Skip payload index setup (useful for troubleshooting).",
    )
    return parser.parse_args()


def main() -> int:
    settings = get_settings()
    args = parse_args(
        default_collection=settings.qdrant.collection,
        default_dimension=settings.qdrant.vector_dimension,
    )

    distance = {
        "cosine": DistanceAlias.COSINE,
        "dot": DistanceAlias.DOT,
        "euclid": DistanceAlias.EUCLID,
    }[args.distance]

    client = build_client(settings)

    created, info = ensure_collection(
        client=client,
        collection=args.collection,
        dimension=args.dimension,
        distance=distance,
        force_recreate=args.force_recreate,
    )

    if not args.skip_indexes:
        ensure_payload_indexes(client, args.collection)

    status = check_health(client, args.collection)

    summary = {
        "collection": args.collection,
        "created": created,
        "dimension": args.dimension,
        "distance": args.distance,
        "status": getattr(status, "value", str(status)),
    }

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
