import sys, os
sys.path.append('src/connectors')
from fabric import FabricConnector
from dotenv import load_dotenv
load_dotenv()

fin = FabricConnector('finance')
rows = fin.execute('SELECT TOP 3 * FROM dbo.financial_transactions')
for r in rows:
    print(r)
