"""Data API endpoints (combined IMS + Jira view)."""
from fastapi import APIRouter

from app.models.combined import HierarchyNode
from app.services.data_combiner import DataCombinerService

router = APIRouter()


@router.get("/data/hierarchy", response_model=list[HierarchyNode])
async def get_hierarchy():
    """
    Return the current combined hierarchy as a tree.
    Returns an empty list if no data has been loaded yet.
    """
    from app.main import combiner as global_combiner

    tree = global_combiner.get_cached_tree()
    return tree or []  # Return empty list instead of 404 — much better for the frontend


@router.get("/data/flat")
async def get_flat_data():
    """Alternative flat view (useful for debugging)."""
    from app.main import combiner as global_combiner

    tree = global_combiner.get_cached_tree() or []

    flat = []

    def flatten(nodes):
        for node in nodes:
            flat.append(node.data.model_dump())
            if node.children:
                flatten(node.children)

    flatten(tree)
    return flat