import os
import struct
from itertools import chain, repeat
import pyodbc
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

class FabricConnector:
    def __init__(self, alias: str):
        alias_upper = alias.upper()
        self.sql_endpoint = os.environ[f"FABRIC_SQL_ENDPOINT_{alias_upper}"]
        self.database     = os.environ[f"FABRIC_LAKEHOUSE_{alias_upper}"]
        self._credential  = AzureCliCredential(
            tenant_id=os.environ.get("AZURE_TENANT_ID")
        )

    def _get_token_bytes(self) -> bytes:
        token     = self._credential.get_token("https://database.windows.net//.default")
        token_utf = bytes(token.token, "UTF-8")
        encoded   = bytes(chain.from_iterable(zip(token_utf, repeat(0))))
        return struct.pack("<i", len(encoded)) + encoded

    def _get_connection(self):
        conn_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={self.sql_endpoint},1433;"
            f"Database={self.database};"
            f"Encrypt=Yes;TrustServerCertificate=No;"
        )
        return pyodbc.connect(conn_str, attrs_before={1256: self._get_token_bytes()})

    def execute(self, sql: str) -> list[dict]:
        conn   = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        cols   = [c[0] for c in cursor.description]
        rows   = [dict(zip(cols, row)) for row in cursor.fetchall()]
        conn.close()
        return rows

    def list_tables(self) -> list[str]:
        rows = self.execute("""
            SELECT TABLE_SCHEMA + '.' + TABLE_NAME AS full_name
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        return [r["full_name"] for r in rows]
