"""
DDL Ingestion Script
====================
Scans all .sql DDL files under udco-cltv/META/scripts/ddl/,
parses them into DDLQuery models, and stores them in MongoDB.

Database : query_builder
Collections : ddl            (root-level DDLs)
              ddl_analytical  (Analytical/ subdirectory DDLs)
"""

import os
import re
import glob
from sp_gen_sdk.model import sql
from sp_gen_sdk.connector.mongo import MongoConnector

# ── Configuration ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DDL_ROOT = os.path.join(BASE_DIR, "udco-cltv", "META", "scripts", "ddl")

MONGO_DB = "query_builder"
COLLECTION_MAP = {
    "root": "ddl",
    "Analytical": "ddl_analytical",
}


# ── Helpers ──────────────────────────────────────────────────────

def strip_options(text: str) -> str:
    """
    Remove all OPTIONS(...) blocks from DDL text, correctly
    handling nested parentheses inside labels = [('a','b'),...].
    """
    result = []
    i = 0
    pattern = re.compile(r'OPTIONS\s*\(', re.IGNORECASE)
    while i < len(text):
        m = pattern.search(text, i)
        if not m:
            result.append(text[i:])
            break
        result.append(text[i:m.start()])
        # Walk forward to find the matching closing paren
        depth = 1
        j = m.end()
        in_single = False
        in_double = False
        while j < len(text) and depth > 0:
            ch = text[j]
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
            j += 1
        i = j
    return ''.join(result)


def extract_create_statement(raw_sql: str) -> str:
    """
    Given raw DDL text that may contain multiple statements
    (e.g. DROP TABLE … ; CREATE TABLE … ;), return only the
    CREATE statement text.  Uses keyword search rather than
    semicolon-splitting to avoid breaking on ';' inside strings.
    """
    # Find the position of the CREATE keyword
    match = re.search(r'\bCREATE\b', raw_sql, re.IGNORECASE)
    if not match:
        raise ValueError("No CREATE statement found in DDL text")
    return raw_sql[match.start():]


def classify_file(filepath: str) -> str:
    """
    Return the collection key based on whether the file lives
    in the Analytical subdirectory or in the root ddl/ folder.
    """
    rel = os.path.relpath(filepath, DDL_ROOT)
    parts = rel.split(os.sep)
    if len(parts) > 1 and parts[0] == "Analytical":
        return "Analytical"
    return "root"


def parse_ddl_file(filepath: str) -> dict | None:
    """
    Read a DDL file, extract the CREATE statement, parse it
    into a DDLQuery model, and return the model as a dict.

    Two-pass strategy:
      1. Try parsing the raw CREATE statement directly.
      2. If sqlglot chokes (e.g. bad quoting in OPTIONS), strip
         all OPTIONS(...) blocks and retry — column descriptions
         will be empty but structure is preserved.
    """
    try:
        raw_sql = sql.Query.extract_file(filepath)
        create_sql = extract_create_statement(raw_sql)

        # Pass 1 – parse as-is
        try:
            ddl_query = sql.DDLQuery.parse(create_sql)
        except Exception:
            # Pass 2 – strip OPTIONS and retry
            sanitized = strip_options(create_sql)
            ddl_query = sql.DDLQuery.parse(sanitized)
            print(f"  ⚠  OPTIONS stripped for {os.path.basename(filepath)} (tokenizer workaround)")

        doc = ddl_query.model_dump()
        doc["ddl_loc"] = filepath
        doc["file_name"] = os.path.basename(filepath)
        return doc
    except Exception as e:
        print(f"  ✗  SKIPPED {filepath}: {e}")
        return None


# ── Main pipeline ────────────────────────────────────────────────

def run(mongo: MongoConnector | None = None):
    """
    Scan, parse, and ingest all DDL files into MongoDB.
    If no MongoConnector is provided, one is created automatically.
    """
    own_connection = mongo is None
    if own_connection:
        mongo = MongoConnector()
        mongo.client()

    # Collect DDL files
    all_sql_files = sorted(
        glob.glob(os.path.join(DDL_ROOT, "**", "*.sql"), recursive=True)
    )
    print(f"\n📂  Found {len(all_sql_files)} DDL files under {DDL_ROOT}\n")

    # Bucket documents by collection
    buckets: dict[str, list[dict]] = {key: [] for key in COLLECTION_MAP}

    for filepath in all_sql_files:
        category = classify_file(filepath)
        doc = parse_ddl_file(filepath)
        if doc:
            doc["category"] = category
            buckets[category].append(doc)
            print(f"  ✓  Parsed {os.path.basename(filepath)}")

    # Insert into MongoDB
    print(f"\n💾  Inserting into MongoDB database '{MONGO_DB}' …")
    for key, docs in buckets.items():
        collection_name = COLLECTION_MAP[key]
        if not docs:
            print(f"  ⏭  {collection_name}: no documents to insert")
            continue
        result = mongo.insert_many(MONGO_DB, collection_name, docs)
        print(f"  ✓  {collection_name}: inserted {len(result.inserted_ids)} documents")

    # Summary
    total = sum(len(d) for d in buckets.values())
    print(f"\n✅  Done — {total} documents ingested into '{MONGO_DB}'.\n")

    if own_connection:
        mongo.disconnect()


# ── Entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    run()
