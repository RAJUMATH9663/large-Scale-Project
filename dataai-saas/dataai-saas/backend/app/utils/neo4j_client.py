from neo4j import GraphDatabase
from app.config import get_settings

settings = get_settings()

_driver = None


def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver


def close_neo4j():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def run_query(query: str, parameters: dict = None):
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [dict(record) for record in result]
