import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ── Configuração da página ──
st.set_page_config(page_title="Dashboard Financeiro", layout="wide")

# ── Categorização expandida ──
CATEGORIAS = [
    (["sabesp", "saneamento"], "Água"),
    (["claro", "tim ", "vivo", "telefonica", "oi fibra"], "Telefone/Internet"),
    (["enel", "cpfl", "cemig", "eletropaulo", "luz", "energia"], "Energia"),
    (["cartoes caixa", "fatura", "nubank", "itaucard", "bradesco cartao"], "Cartão de Crédito"),
    (["boleto"], "Boletos Diversos"),
    (["transferência enviada", "pix enviado", "ted enviada", "transf enviada"], "Transferências Enviadas"),
    (["transferência recebida", "pix recebido", "ted recebida", "salario", "salário", "transf recebida"], "Recebimentos"),
    (["uber", "99", "cabify", "metro", "bilhete unico"], "Transporte"),
    (["ifood", "rappi", "mercado", "supermercado", "padaria", "restaurante"], "Alimentação"),
]

def categorizar(desc):
    d = str(desc).lower()
    for palavras, categoria in CATEGORIAS:
        if any(p in d for p in palavras):
            return categoria
    return "Outros"


def parse_valor_br(v):
    """Converte valores no formato BR (1.234,56) e outros formatos comuns."""
    if pd.isna(v):
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("\xa0", "")
    # Remove R$ e espaços
    s = s.replace("R$", "").replace("r$", "").strip()
    if not s:
        return float("nan")
    # Formato BR: 1.234,56 → 1234.56
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def encontrar_coluna(colunas, candidatos):
    """Busca flexível de colunas por palavras-chave."""
    colunas_lower = {c: c.lower().strip() for c in colunas}
    # Match exato primeiro
    for cand in candidatos:
        for col_orig, col_low in colunas_lower.items():
            if col_low == cand:
                return col_orig
    # Match parcial
    for cand in candidatos:
        for col_orig, col_low in colunas_lower.items():
            if cand in col_low:
                return col_orig
    return None


def ler_csv_robusto(uploaded_file):
    """Tenta múltiplos encodings e separadores."""
    conteudo = uploaded_file.read()
    uploaded_file.seek(0)

    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin1"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(conteudo),
                    encoding=enc,
                    sep=sep,
                    skipinitialspace=True,
                )
                # Descarta se leu tudo numa coluna só (separador errado)
                if len(df.columns) >= 3:
                    return df
            except Exception:
                continue
    return None


def processar(arquivos):
    """Pipeline completo: leitura → limpeza → categorização."""
    dfs = []
    erros = []
    for arq in arquivos:
        df = ler_csv_robusto(arq)
        if df is not None:
            dfs.append(df)
        else:
            erros.append(arq.name)

    if not dfs:
        return None, erros

    df = pd.concat(dfs, ignore_index=True)

    # Normaliza nomes de colunas
    df.columns = df.columns.str.strip().str.lower()
    df = df.loc[:, ~df.columns.duplicated()]

    # Debug: mostra colunas encontradas
    st.caption(f"Colunas detectadas: {list(df.columns)}")

    # Detecta colunas principais
    col_data = encontrar_coluna(df.columns, ["data", "date", "dt", "data lançamento", "data lancamento"])
    col_valor = encontrar_coluna(df.columns, ["valor", "value", "vlr", "valor (r$)", "quantia", "amount"])
    col_desc = encontrar_coluna(df.columns, ["descricao", "descrição", "descrição", "historico", "histórico", "hist", "lancamento", "lançamento"])

    if not col_valor:
        st.error(f"Coluna de valor não encontrada. Colunas disponíveis: {list(df.columns)}")
        return None, erros
    if not col_data:
        st.error(f"Coluna de data não encontrada. Colunas disponíveis: {list(df.columns)}")
        return None, erros

    # Padroniza nomes
    df = df.rename(columns={col_data: "data", col_valor: "valor"})
    if col_desc:
        df = df.rename(columns={col_desc: "descricao"})
    else:
        df["descricao"] = "Sem descrição"

    # Converte tipos
    df["valor"] = df["valor"].apply(parse_valor_br)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")

    # Remove linhas inválidas
    antes = len(df)
    df = df.dropna(subset=["data", "valor"])
    removidas = antes - len(df)
    if removidas > 0:
        st.warning(f"{removidas} linhas removidas por data ou valor inválido.")

    # Colunas derivadas
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["categoria"] = df["descricao"].apply(categorizar)
    df = df.sort_values("data").reset_index(drop=True)

    return df, erros


# ══════════════════════════════════════
# INTERFACE
# ══════════════════════════════════════
st.title("📊 Dashboard Financeiro")
st.markdown("Consolide seus extratos bancários e visualize seu fluxo de caixa.")

arquivos = st.file_uploader(
    "Arraste seus extratos CSV aqui",
    type=["csv"],
    accept_multiple_files=True,
)

if not arquivos:
    st.info("Faça upload de um ou mais arquivos CSV de extrato bancário para começar.")
    st.stop()

df, erros = processar(arquivos)

if erros:
    st.error(f"Não foi possível ler: {', '.join(erros)}")

if df is None or df.empty:
    st.error("Nenhuma transação válida encontrada nos arquivos.")
    st.stop()

# ── KPIs ──
entradas = df[df["valor"] > 0]["valor"].sum()
saidas = df[df["valor"] < 0]["valor"].sum()
saldo = entradas + saidas

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entradas", f"R$ {entradas:,.2f}")
c2.metric("Saídas", f"R$ {abs(saidas):,.2f}")
c3.metric("Saldo Líquido", f"R$ {saldo:,.2f}", delta=f"{'↑' if saldo >= 0 else '↓'}")
c4.metric("Transações", f"{len(df):,}")

st.divider()

# ── 1. Fluxo mensal: entradas vs saídas separadas ──
st.subheader("Fluxo de Caixa Mensal")

mensal = df.copy()
mensal["tipo"] = mensal["valor"].apply(lambda v: "Entradas" if v > 0 else "Saídas")
mensal["abs_valor"] = mensal["valor"].abs()
mensal_agg = mensal.groupby(["mes", "tipo"], as_index=False)["abs_valor"].sum()

fig1 = px.bar(
    mensal_agg, x="mes", y="abs_valor", color="tipo",
    barmode="group",
    color_discrete_map={"Entradas": "#1a6b3c", "Saídas": "#d32f2f"},
    labels={"abs_valor": "Valor (R$)", "mes": "Mês"},
)
fig1.update_layout(legend_title_text="", margin=dict(t=10))
st.plotly_chart(fig1, use_container_width=True)

# ── Layout 2 colunas ──
col_esq, col_dir = st.columns(2)

# ── 2. Pizza de categorias (só saídas) ──
with col_esq:
    st.subheader("Distribuição de Gastos")
    saidas_df = df[df["valor"] < 0].copy()
    saidas_df["abs_valor"] = saidas_df["valor"].abs()
    cat_agg = saidas_df.groupby("categoria", as_index=False)["abs_valor"].sum()
    cat_agg = cat_agg.sort_values("abs_valor", ascending=False)

    fig2 = px.pie(
        cat_agg, values="abs_valor", names="categoria",
        hole=0.4,
    )
    fig2.update_traces(textinfo="percent+label", textposition="outside")
    fig2.update_layout(showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig2, use_container_width=True)

# ── 3. Top 5 despesas (corrigido: nsmallest) ──
with col_dir:
    st.subheader("Top 5 Maiores Despesas")
    top5 = saidas_df.nsmallest(5, "valor").copy()
    top5["abs_valor"] = top5["valor"].abs()
    top5["descricao_curta"] = top5["descricao"].str[:45]

    fig3 = px.bar(
        top5, y="descricao_curta", x="abs_valor",
        orientation="h",
        color_discrete_sequence=["#E91E63"],
        labels={"abs_valor": "Valor (R$)", "descricao_curta": ""},
    )
    fig3.update_layout(margin=dict(t=10))
    st.plotly_chart(fig3, use_container_width=True)

# ── 4. Gastos por categoria ao longo do tempo ──
st.subheader("Evolução de Gastos por Categoria")
cat_tempo = saidas_df.groupby(["mes", "categoria"], as_index=False)["abs_valor"].sum()

fig4 = px.bar(
    cat_tempo, x="mes", y="abs_valor", color="categoria",
    barmode="stack",
    labels={"abs_valor": "Valor (R$)", "mes": "Mês"},
)
fig4.update_layout(legend_title_text="", margin=dict(t=10))
st.plotly_chart(fig4, use_container_width=True)

# ── 5. Saldo acumulado ──
st.subheader("Saldo Acumulado")
saldo_mensal = df.groupby("mes", as_index=False)["valor"].sum()
saldo_mensal["saldo_acumulado"] = saldo_mensal["valor"].cumsum()

fig5 = px.line(
    saldo_mensal, x="mes", y="saldo_acumulado",
    markers=True,
    color_discrete_sequence=["#1a6b3c"],
    labels={"saldo_acumulado": "Saldo (R$)", "mes": "Mês"},
)
fig5.update_layout(margin=dict(t=10))
st.plotly_chart(fig5, use_container_width=True)

# ── Tabela detalhada ──
with st.expander("Ver todas as transações"):
    st.dataframe(
        df[["data", "descricao", "valor", "categoria", "mes"]].sort_values("data", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

# ── Download do CSV consolidado ──
csv_out = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="Baixar CSV consolidado",
    data=csv_out,
    file_name="extratos_unificados.csv",
    mime="text/csv",
)