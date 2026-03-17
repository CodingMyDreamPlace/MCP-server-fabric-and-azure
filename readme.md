# MCP Server — Microsoft Fabric + Azure AI

A production-ready **AI agent** that connects GPT-4o to Microsoft Fabric data warehouses using Azure AD authentication. The agent answers business questions in natural language by querying real SQL data from Microsoft Fabric.

## Architecture

```
User (terminal)
      ↓
orchestrator.py  ←→  GPT-4o (Azure AI Foundry)
      ↓
FabricConnector (fabric.py)
      ↓
Microsoft Fabric SQL Warehouses
   ├── LH_Operations  (dbo.fact_revenue)
   └── LH_Finance     (dbo.financial_transactions)
```

## Features

- 🤖 **GPT-4o agent** via Azure AI Foundry with tool-calling loop
- 🔐 **Passwordless auth** via `DefaultAzureCredential` (Azure CLI / Managed Identity)
- 🏭 **Dual warehouse** support — Operations and Finance as separate tools
- 🔄 **Cross-warehouse queries** — compare gross vs net revenue in one call
- 🧩 **Semantic layer** — entity config via YAML (`config/entities/`)
- 💬 **Terminal chat interface** — ask questions in natural language, get data-backed answers

## Project Structure

```
├── config/
│   └── entities/
│       └── revenue.yaml            # Semantic entity definitions
├── src/
│   ├── agents/
│   │   └── orchestrator.py         # GPT-4o agent with tool-calling loop
│   ├── connectors/
│   │   └── fabric.py               # Fabric SQL connector with token auth
│   ├── gateway/
│   │   └── server.py               # MCP server (FastMCP)
│   └── semantic/
│       └── loader.py               # YAML entity loader
├── test_fabric.py                  # Connection test for both warehouses
├── .env.example                    # Environment variables template
└── requirements.txt
```

## Data Schema

**LH_Operations** → `dbo.fact_revenue`
| Column | Type | Values |
|--------|------|--------|
| region | TEXT | Lima, Cusco, Arequipa |
| gross_amount | FLOAT | — |
| billing_date | DATE | — |

**LH_Finance** → `dbo.financial_transactions`
| Column | Type | Values |
|--------|------|--------|
| branch_id | TEXT | Lima, Cusco, Arequipa |
| net_revenue_usd | FLOAT | — |
| transaction_date | DATE | — |

## Prerequisites

- Python 3.10+
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged in
- Microsoft Fabric workspace with SQL Warehouses
- ODBC Driver 18 for SQL Server
- Azure AI Foundry resource with GPT-4o deployed

## Setup

**1. Clone and install**
```bash
git clone https://github.com/CodingMyDreamPlace/MCP-server-fabric-and-azure.git
cd MCP-server-fabric-and-azure
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
```

Edit `.env`:
```env
FABRIC_SQL_ENDPOINT_OPERATIONS=<your-operations-endpoint>.datawarehouse.fabric.microsoft.com
FABRIC_LAKEHOUSE_OPERATIONS=LH_Operations

FABRIC_SQL_ENDPOINT_FINANCE=<your-finance-endpoint>.datawarehouse.fabric.microsoft.com
FABRIC_LAKEHOUSE_FINANCE=LH_Finance

AZURE_TENANT_ID=<your-tenant-id>
AZURE_SUBSCRIPTION_ID=<your-subscription-id>

# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT=<your-foundry-endpoint>
MODEL_DEPLOYMENT=gpt-4o
MCP_SERVER_URL=http://localhost:8000
```

**3. Login to Azure**
```bash
az login --tenant <your-tenant-id>
```

**4. Test the connection**
```bash
python test_fabric.py
```

Expected output:
```
=== OPERATIONS ===
['dbo.fact_revenue']
[{'region': 'Lima', 'gross_amount': 15000.0, ...}]

=== FINANCE ===
['dbo.financial_transactions']
[{'branch_id': 'Lima', 'net_revenue_usd': 14100.0, ...}]
```

**5. Run the agent**
```bash
python src/agents/orchestrator.py
```

Example session:
```
FabricAgent listo. 'exit' para salir.

Tú: ¿Cuánto revenue tuvo Lima en enero?
Agente: Lima generó S/. 15,000 en gross revenue durante enero 2026...

Tú: Compara gross vs net de todas las regiones
Agente: Lima: gross $27,300 vs net $25,600 (margen ~6.2%)...
```

## Agent Tools

| Tool | Warehouse | Use case |
|------|-----------|----------|
| `query_operations` | LH_Operations | Revenue, sales, billing by region |
| `query_finance` | LH_Finance | Net revenue, margins, financial KPIs |
| `query_cross` | Both | Cross-warehouse comparisons |