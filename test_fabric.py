from dotenv import load_dotenv
load_dotenv()

from src.connectors.fabric import FabricConnector

print("=== OPERATIONS ===")
c1 = FabricConnector("operations")
print(c1.list_tables())
print(c1.execute("SELECT * FROM dbo.fact_revenue"))

print("\n=== FINANCE ===")
c2 = FabricConnector("finance")
print(c2.list_tables())
print(c2.execute("SELECT * FROM dbo.financial_transactions"))