import os, json, sys
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

# ── Importar tu FabricConnector ───────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "connectors"))
from fabric import FabricConnector

_ops = FabricConnector("operations")
_fin = FabricConnector("finance")

# ── Dispatcher: conecta tool name → FabricConnector.execute() ────────────────
def execute_tool(name: str, args: dict) -> str:
    try:
        if name == "query_operations":
            rows = _ops.execute(args["sql"])
        elif name == "query_finance":
            rows = _fin.execute(args["sql"])
        elif name == "query_cross":
            rows = {
                "operations": _ops.execute(args["operations_sql"]),
                "finance":    _fin.execute(args["finance_sql"]),
            }
        else:
            return json.dumps({"error": f"Tool desconocida: {name}"})
        return json.dumps(rows, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ── Tool schemas (formato correcto para openai SDK) ───────────────────────────
TOOLS = [
    {"type": "function", "function": {
        "name": "query_operations",
        "description": "Consulta LH_Operations en Microsoft Fabric. Revenue, ventas y métricas por región: Lima, Cusco, Arequipa.",
        "parameters": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SQL válido para el warehouse de operaciones"}},
            "required": ["sql"],
        },
    }},
    {"type": "function", "function": {
        "name": "query_finance",
        "description": "Consulta LH_Finance en Microsoft Fabric. Costos, márgenes y KPIs financieros por región.",
        "parameters": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "SQL válido para el warehouse financiero"}},
            "required": ["sql"],
        },
    }},
    {"type": "function", "function": {
        "name": "query_cross",
        "description": "Consulta ambos warehouses simultáneamente. Úsalo cuando la pregunta compare operaciones con finanzas.",
        "parameters": {
            "type": "object",
            "properties": {
                "operations_sql": {"type": "string", "description": "SQL para LH_Operations"},
                "finance_sql":    {"type": "string", "description": "SQL para LH_Finance"},
            },
            "required": ["operations_sql", "finance_sql"],
        },
    }},
]

SYSTEM_PROMPT = """Eres FabricAgent, asistente de análisis de datos empresariales peruanos.
Tienes acceso a datos reales en Microsoft Fabric de Lima, Cusco y Arequipa.

SCHEMA EXACTO — usa SIEMPRE estos nombres:

LH_Operations → tabla: dbo.fact_revenue
  Columnas: region (TEXT), gross_amount (FLOAT), billing_date (DATE)
  Regiones: 'Lima', 'Cusco', 'Arequipa'

LH_Finance → tabla: dbo.financial_transactions
  Columnas: branch_id (TEXT), net_revenue_usd (FLOAT), transaction_date (DATE)
  Valores de branch_id: 'Lima', 'Cusco', 'Arequipa'

SQLs de ejemplo:
  SELECT region, SUM(gross_amount) AS total FROM dbo.fact_revenue GROUP BY region
  SELECT branch_id, SUM(net_revenue_usd) AS total FROM dbo.financial_transactions GROUP BY branch_id
  SELECT SUM(gross_amount) FROM dbo.fact_revenue WHERE region = 'Lima'

Reglas:
1. SIEMPRE usa el nombre completo de tabla: dbo.fact_revenue o dbo.financial_transactions
2. En operations usa columna 'region'; en finance usa columna 'branch_id'
3. Usa query_cross cuando la pregunta compare operaciones con finanzas
4. Responde en español con los datos encontrados y un análisis breve
5. Nunca inventes datos — solo reporta lo que devuelven las herramientas"""


# ── Cliente AzureOpenAI (funciona con tu recurso CognitiveServices) ───────────
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)
openai_client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    azure_ad_token_provider=token_provider,
    api_version="2025-01-01-preview",
)

# ── Función principal ─────────────────────────────────────────────────────────
def ask(question: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": question},
    ]
    while True:
        response = openai_client.chat.completions.create(
            model=os.environ.get("MODEL_DEPLOYMENT", "gpt-4o"),
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:       # respuesta final — sin más tool calls
            return msg.content

        messages.append(msg)
        for tc in msg.tool_calls:    # ejecutar cada tool y devolver resultado
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result,
            })

# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("FabricAgent listo. 'exit' para salir.\n")
    while True:
        q = input("Tú: ").strip()
        if not q or q.lower() in ("exit", "salir"):
            break
        print(f"\nAgente: {ask(q)}\n")
