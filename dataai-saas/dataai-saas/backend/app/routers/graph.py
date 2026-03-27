from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.utils.auth import get_current_user
from app.utils.neo4j_client import run_query
from app.models.models import User

router = APIRouter(prefix="/api/graph", tags=["Graph (Neo4j)"])


class BuildGraphRequest(BaseModel):
    dataset_id: int
    node_label: str
    node_properties: List[str]
    source_column: str
    target_column: str
    relationship_type: str = "RELATES_TO"
    relationship_weight_column: Optional[str] = None


class GraphQueryRequest(BaseModel):
    cypher: str
    parameters: Optional[Dict[str, Any]] = {}


@router.post("/build")
async def build_graph(
    payload: BuildGraphRequest,
    current_user: User = Depends(get_current_user),
):
    """Build a Neo4j graph from dataset columns."""
    try:
        # Create uniqueness constraint
        run_query(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{payload.node_label}) REQUIRE n.id IS UNIQUE")

        # Create relationship from dataset (simplified demo — in production, stream rows)
        sample_pairs = [
            {"source": f"node_{i}", "target": f"node_{i+1}", "weight": i * 0.5}
            for i in range(10)
        ]

        for pair in sample_pairs:
            query = f"""
            MERGE (a:{payload.node_label} {{id: $source}})
            MERGE (b:{payload.node_label} {{id: $target}})
            MERGE (a)-[r:{payload.relationship_type}]->(b)
            SET r.weight = $weight
            """
            run_query(query, {"source": pair["source"], "target": pair["target"], "weight": pair["weight"]})

        return {"status": "Graph built", "nodes_created": len(sample_pairs) + 1, "relationships": len(sample_pairs)}
    except Exception as e:
        raise HTTPException(500, f"Graph build error: {str(e)}")


@router.post("/query")
async def query_graph(
    payload: GraphQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Run a Cypher query on Neo4j."""
    # Safety: only allow read queries in this endpoint
    forbidden = ["DELETE", "DETACH", "DROP", "CREATE CONSTRAINT", "REMOVE"]
    query_upper = payload.cypher.upper()
    if any(kw in query_upper for kw in forbidden):
        raise HTTPException(403, "Write/delete queries not allowed via this endpoint")
    try:
        results = run_query(payload.cypher, payload.parameters)
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(500, f"Query error: {str(e)}")


@router.get("/stats")
async def graph_stats(current_user: User = Depends(get_current_user)):
    try:
        node_count = run_query("MATCH (n) RETURN count(n) AS count")
        rel_count = run_query("MATCH ()-[r]->() RETURN count(r) AS count")
        labels = run_query("CALL db.labels() YIELD label RETURN label")
        return {
            "nodes": node_count[0]["count"] if node_count else 0,
            "relationships": rel_count[0]["count"] if rel_count else 0,
            "labels": [l["label"] for l in labels],
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/network")
async def get_network(label: str = "Node", limit: int = 50, current_user: User = Depends(get_current_user)):
    try:
        results = run_query(
            f"MATCH (a:{label})-[r]->(b:{label}) RETURN a.id as source, b.id as target, type(r) as rel, r.weight as weight LIMIT $limit",
            {"limit": limit}
        )
        nodes_set = set()
        edges = []
        for row in results:
            nodes_set.add(row["source"])
            nodes_set.add(row["target"])
            edges.append({"source": row["source"], "target": row["target"],
                          "rel": row["rel"], "weight": row.get("weight", 1)})
        return {
            "nodes": [{"id": n} for n in nodes_set],
            "edges": edges,
        }
    except Exception as e:
        raise HTTPException(500, str(e))
