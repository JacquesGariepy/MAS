"""
Database Tool for MAS Agents
Provides database operations and query capabilities
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
import sqlite3
import asyncpg
import pymongo
from contextlib import asynccontextmanager

from .base_tool import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class DatabaseTool(BaseTool):
    """Tool for database operations"""
    
    def __init__(self, agent_id: str, workspace_root: str = "/app/agent_workspace"):
        super().__init__(
            name="DatabaseTool",
            description="Perform database operations",
            parameters={
                "action": {
                    "type": "string",
                    "enum": ["connect", "query", "insert", "update", "delete", 
                            "create_table", "drop_table", "schema", "backup"],
                    "description": "Database action to perform"
                },
                "db_type": {
                    "type": "string",
                    "enum": ["sqlite", "postgresql", "mongodb"],
                    "description": "Database type"
                },
                "connection": {
                    "type": "object",
                    "description": "Connection parameters"
                },
                "query": {
                    "type": "string",
                    "description": "SQL query or MongoDB query"
                },
                "table": {
                    "type": "string",
                    "description": "Table/collection name"
                },
                "data": {
                    "type": "object",
                    "description": "Data to insert/update"
                },
                "condition": {
                    "type": "object",
                    "description": "Condition for update/delete"
                },
                "schema": {
                    "type": "object",
                    "description": "Table schema definition"
                }
            },
            required=["action", "db_type"]
        )
        self.agent_id = agent_id
        self.workspace_root = Path(workspace_root)
        self.db_dir = self.workspace_root / "databases"
        self.db_dir.mkdir(exist_ok=True)
        
        # Connection pools
        self.connections = {}
        
    async def execute(self, **kwargs) -> ToolResult:
        """Execute database tool action"""
        action = kwargs.get("action")
        db_type = kwargs.get("db_type")
        
        try:
            if action == "connect":
                return await self._connect(kwargs)
            elif action == "query":
                return await self._query(kwargs)
            elif action == "insert":
                return await self._insert(kwargs)
            elif action == "update":
                return await self._update(kwargs)
            elif action == "delete":
                return await self._delete(kwargs)
            elif action == "create_table":
                return await self._create_table(kwargs)
            elif action == "drop_table":
                return await self._drop_table(kwargs)
            elif action == "schema":
                return await self._get_schema(kwargs)
            elif action == "backup":
                return await self._backup(kwargs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            logger.error(f"Database tool error: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
            
    async def _connect(self, params: Dict[str, Any]) -> ToolResult:
        """Establish database connection"""
        db_type = params.get("db_type")
        connection_params = params.get("connection", {})
        
        try:
            if db_type == "sqlite":
                db_path = connection_params.get("path", str(self.db_dir / "default.db"))
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self.connections[db_type] = conn
                
            elif db_type == "postgresql":
                conn = await asyncpg.connect(
                    host=connection_params.get("host", "localhost"),
                    port=connection_params.get("port", 5432),
                    user=connection_params.get("user", "postgres"),
                    password=connection_params.get("password", ""),
                    database=connection_params.get("database", "postgres")
                )
                self.connections[db_type] = conn
                
            elif db_type == "mongodb":
                client = pymongo.MongoClient(
                    host=connection_params.get("host", "localhost"),
                    port=connection_params.get("port", 27017)
                )
                db_name = connection_params.get("database", "test")
                self.connections[db_type] = client[db_name]
                
            return ToolResult(
                success=True,
                data={
                    "message": f"Connected to {db_type} database",
                    "connection_id": db_type
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Connection failed: {str(e)}"
            )
            
    async def _query(self, params: Dict[str, Any]) -> ToolResult:
        """Execute a query"""
        db_type = params.get("db_type")
        query = params.get("query")
        
        if not query:
            return ToolResult(success=False, error="Query required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                cursor = conn.execute(query)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                results = [dict(zip(columns, row)) for row in rows]
                
            elif db_type == "postgresql":
                rows = await conn.fetch(query)
                results = [dict(row) for row in rows]
                
            elif db_type == "mongodb":
                # Parse MongoDB-style query
                collection_name = params.get("table", "default")
                collection = conn[collection_name]
                
                if isinstance(query, str):
                    query_dict = json.loads(query)
                else:
                    query_dict = query
                    
                cursor = collection.find(query_dict)
                results = list(cursor)
                
                # Convert ObjectId to string
                for result in results:
                    if "_id" in result:
                        result["_id"] = str(result["_id"])
                        
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "count": len(results)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Query failed: {str(e)}"
            )
            
    async def _insert(self, params: Dict[str, Any]) -> ToolResult:
        """Insert data into database"""
        db_type = params.get("db_type")
        table = params.get("table")
        data = params.get("data")
        
        if not table or not data:
            return ToolResult(success=False, error="Table and data required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ", ".join(["?" for _ in values])
                
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                cursor = conn.execute(query, values)
                conn.commit()
                
                return ToolResult(
                    success=True,
                    data={
                        "inserted_id": cursor.lastrowid,
                        "rows_affected": cursor.rowcount
                    }
                )
                
            elif db_type == "postgresql":
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
                
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *"
                result = await conn.fetchrow(query, *values)
                
                return ToolResult(
                    success=True,
                    data={
                        "inserted": dict(result) if result else None
                    }
                )
                
            elif db_type == "mongodb":
                collection = conn[table]
                
                if isinstance(data, list):
                    result = collection.insert_many(data)
                    inserted_ids = [str(id) for id in result.inserted_ids]
                else:
                    result = collection.insert_one(data)
                    inserted_ids = [str(result.inserted_id)]
                    
                return ToolResult(
                    success=True,
                    data={
                        "inserted_ids": inserted_ids,
                        "count": len(inserted_ids)
                    }
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Insert failed: {str(e)}"
            )
            
    async def _update(self, params: Dict[str, Any]) -> ToolResult:
        """Update data in database"""
        db_type = params.get("db_type")
        table = params.get("table")
        data = params.get("data")
        condition = params.get("condition", {})
        
        if not table or not data:
            return ToolResult(success=False, error="Table and data required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
                
                query = f"UPDATE {table} SET {set_clause}"
                values = list(data.values())
                
                if where_clause:
                    query += f" WHERE {where_clause}"
                    values.extend(list(condition.values()))
                    
                cursor = conn.execute(query, values)
                conn.commit()
                
                return ToolResult(
                    success=True,
                    data={"rows_affected": cursor.rowcount}
                )
                
            elif db_type == "postgresql":
                set_clause = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
                values = list(data.values())
                
                query = f"UPDATE {table} SET {set_clause}"
                
                if condition:
                    where_parts = []
                    for i, (k, v) in enumerate(condition.items()):
                        where_parts.append(f"{k} = ${len(values) + i + 1}")
                        values.append(v)
                    query += f" WHERE {' AND '.join(where_parts)}"
                    
                result = await conn.execute(query, *values)
                
                return ToolResult(
                    success=True,
                    data={"rows_affected": int(result.split()[-1])}
                )
                
            elif db_type == "mongodb":
                collection = conn[table]
                result = collection.update_many(condition, {"$set": data})
                
                return ToolResult(
                    success=True,
                    data={
                        "matched_count": result.matched_count,
                        "modified_count": result.modified_count
                    }
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Update failed: {str(e)}"
            )
            
    async def _delete(self, params: Dict[str, Any]) -> ToolResult:
        """Delete data from database"""
        db_type = params.get("db_type")
        table = params.get("table")
        condition = params.get("condition", {})
        
        if not table:
            return ToolResult(success=False, error="Table required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                where_clause = " AND ".join([f"{k} = ?" for k in condition.keys()])
                query = f"DELETE FROM {table}"
                values = []
                
                if where_clause:
                    query += f" WHERE {where_clause}"
                    values = list(condition.values())
                    
                cursor = conn.execute(query, values)
                conn.commit()
                
                return ToolResult(
                    success=True,
                    data={"rows_affected": cursor.rowcount}
                )
                
            elif db_type == "postgresql":
                query = f"DELETE FROM {table}"
                values = []
                
                if condition:
                    where_parts = []
                    for i, (k, v) in enumerate(condition.items()):
                        where_parts.append(f"{k} = ${i + 1}")
                        values.append(v)
                    query += f" WHERE {' AND '.join(where_parts)}"
                    
                result = await conn.execute(query, *values)
                
                return ToolResult(
                    success=True,
                    data={"rows_affected": int(result.split()[-1])}
                )
                
            elif db_type == "mongodb":
                collection = conn[table]
                result = collection.delete_many(condition)
                
                return ToolResult(
                    success=True,
                    data={"deleted_count": result.deleted_count}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Delete failed: {str(e)}"
            )
            
    async def _create_table(self, params: Dict[str, Any]) -> ToolResult:
        """Create a new table"""
        db_type = params.get("db_type")
        table = params.get("table")
        schema = params.get("schema", {})
        
        if not table:
            return ToolResult(success=False, error="Table name required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                columns = []
                for col_name, col_def in schema.items():
                    col_type = col_def.get("type", "TEXT")
                    constraints = []
                    
                    if col_def.get("primary_key"):
                        constraints.append("PRIMARY KEY")
                    if col_def.get("not_null"):
                        constraints.append("NOT NULL")
                    if col_def.get("unique"):
                        constraints.append("UNIQUE")
                        
                    col_sql = f"{col_name} {col_type}"
                    if constraints:
                        col_sql += " " + " ".join(constraints)
                    columns.append(col_sql)
                    
                query = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
                conn.execute(query)
                conn.commit()
                
            elif db_type == "postgresql":
                columns = []
                for col_name, col_def in schema.items():
                    col_type = col_def.get("type", "TEXT")
                    constraints = []
                    
                    if col_def.get("primary_key"):
                        constraints.append("PRIMARY KEY")
                    if col_def.get("not_null"):
                        constraints.append("NOT NULL")
                    if col_def.get("unique"):
                        constraints.append("UNIQUE")
                        
                    col_sql = f"{col_name} {col_type}"
                    if constraints:
                        col_sql += " " + " ".join(constraints)
                    columns.append(col_sql)
                    
                query = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
                await conn.execute(query)
                
            elif db_type == "mongodb":
                # MongoDB doesn't require explicit table creation
                # But we can create indexes
                collection = conn[table]
                
                for field, definition in schema.items():
                    if definition.get("index"):
                        collection.create_index(field)
                    if definition.get("unique"):
                        collection.create_index(field, unique=True)
                        
            return ToolResult(
                success=True,
                data={"message": f"Table {table} created successfully"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Create table failed: {str(e)}"
            )
            
    async def _drop_table(self, params: Dict[str, Any]) -> ToolResult:
        """Drop a table"""
        db_type = params.get("db_type")
        table = params.get("table")
        
        if not table:
            return ToolResult(success=False, error="Table name required")
            
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                conn.execute(f"DROP TABLE IF EXISTS {table}")
                conn.commit()
                
            elif db_type == "postgresql":
                await conn.execute(f"DROP TABLE IF EXISTS {table}")
                
            elif db_type == "mongodb":
                conn[table].drop()
                
            return ToolResult(
                success=True,
                data={"message": f"Table {table} dropped successfully"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Drop table failed: {str(e)}"
            )
            
    async def _get_schema(self, params: Dict[str, Any]) -> ToolResult:
        """Get database schema information"""
        db_type = params.get("db_type")
        table = params.get("table")
        
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        try:
            if db_type == "sqlite":
                if table:
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    columns = []
                    for row in cursor:
                        columns.append({
                            "name": row[1],
                            "type": row[2],
                            "not_null": bool(row[3]),
                            "default": row[4],
                            "primary_key": bool(row[5])
                        })
                    schema = {table: columns}
                else:
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor]
                    schema = {"tables": tables}
                    
            elif db_type == "postgresql":
                if table:
                    query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    """
                    rows = await conn.fetch(query, table)
                    columns = []
                    for row in rows:
                        columns.append({
                            "name": row["column_name"],
                            "type": row["data_type"],
                            "nullable": row["is_nullable"] == "YES",
                            "default": row["column_default"]
                        })
                    schema = {table: columns}
                else:
                    query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                    rows = await conn.fetch(query)
                    tables = [row["tablename"] for row in rows]
                    schema = {"tables": tables}
                    
            elif db_type == "mongodb":
                if table:
                    collection = conn[table]
                    # Get a sample document to infer schema
                    sample = collection.find_one()
                    if sample:
                        schema = {table: list(sample.keys())}
                    else:
                        schema = {table: []}
                else:
                    collections = conn.list_collection_names()
                    schema = {"collections": collections}
                    
            return ToolResult(
                success=True,
                data={"schema": schema}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Get schema failed: {str(e)}"
            )
            
    async def _backup(self, params: Dict[str, Any]) -> ToolResult:
        """Backup database"""
        db_type = params.get("db_type")
        
        conn = self.connections.get(db_type)
        if not conn:
            return ToolResult(success=False, error=f"No connection for {db_type}")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_dir / f"backup_{db_type}_{timestamp}"
        
        try:
            if db_type == "sqlite":
                # SQLite backup
                backup_conn = sqlite3.connect(f"{backup_path}.db")
                conn.backup(backup_conn)
                backup_conn.close()
                
            elif db_type == "postgresql":
                # Export to JSON for simplicity
                tables_query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                tables = await conn.fetch(tables_query)
                
                backup_data = {}
                for table in tables:
                    table_name = table["tablename"]
                    rows = await conn.fetch(f"SELECT * FROM {table_name}")
                    backup_data[table_name] = [dict(row) for row in rows]
                    
                with open(f"{backup_path}.json", "w") as f:
                    json.dump(backup_data, f, indent=2, default=str)
                    
            elif db_type == "mongodb":
                # Export collections to JSON
                backup_data = {}
                for collection_name in conn.list_collection_names():
                    collection = conn[collection_name]
                    documents = list(collection.find())
                    # Convert ObjectId to string
                    for doc in documents:
                        if "_id" in doc:
                            doc["_id"] = str(doc["_id"])
                    backup_data[collection_name] = documents
                    
                with open(f"{backup_path}.json", "w") as f:
                    json.dump(backup_data, f, indent=2)
                    
            return ToolResult(
                success=True,
                data={
                    "message": f"Backup created successfully",
                    "backup_path": str(backup_path)
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Backup failed: {str(e)}"
            )
            
    async def cleanup(self):
        """Clean up database connections"""
        for db_type, conn in self.connections.items():
            try:
                if db_type == "sqlite":
                    conn.close()
                elif db_type == "postgresql":
                    await conn.close()
                elif db_type == "mongodb":
                    conn.client.close()
            except Exception as e:
                logger.error(f"Error closing {db_type} connection: {e}")