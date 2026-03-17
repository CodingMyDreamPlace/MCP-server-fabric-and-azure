import os
import struct
import pyodbc
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("fabric-agent")


def get_conn(server: str, database: str):
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        f"Encrypt=yes;"
    )
    conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
    return conn


@mcp.tool()
def query_operations(sql: str) -> list[dict]:
    """
    Ejecuta una consulta SQL en el warehouse OPERATIONS.
    Tabla principal: dbo.fact_revenue (region, gross_amount, billing_date)
    """
    conn = get_conn(
        os.environ["FABRIC_SQL_ENDPOINT_OPERATIONS"],
        os.environ["FABRIC_LAKEHOUSE_OPERATIONS"],
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [d[0] for d in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return rows


@mcp.tool()
def query_finance(sql: str) -> list[dict]:
    """
    Ejecuta una consulta SQL en el warehouse FINANCE.
    Tabla principal: dbo.financial_transactions (branch_id, net_revenue_usd, transaction_date)
    """
    conn = get_conn(
        os.environ["FABRIC_SQL_ENDPOINT_FINANCE"],
        os.environ["FABRIC_LAKEHOUSE_FINANCE"],
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [d[0] for d in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return rows


@mcp.tool()
def query_cross(sql_ops: str, sql_fin: str) -> dict:
    """
    Ejecuta queries en ambos warehouses y retorna los dos resultados juntos.
    Útil para comparar gross_amount (OPERATIONS) vs net_revenue_usd (FINANCE).
    """
    ops = query_operations(sql_ops)
    fin = query_finance(sql_fin)
    return {"operations": ops, "finance": fin}


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)