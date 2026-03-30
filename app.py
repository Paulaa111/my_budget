import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import calendar
import os

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mój Budżet",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Dark minimal theme */
.stApp {
    background-color: #0d0d0d;
    color: #f0ece0;
}

.main-header {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -2px;
    color: #f0ece0;
    margin-bottom: 0;
}

.sub-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #6b6b6b;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

.big-number {
    font-family: 'Space Mono', monospace;
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
}

.big-number.positive { color: #b8f5a0; }
.big-number.warning  { color: #f5d78a; }
.big-number.negative { color: #f5a0a0; }

.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.metric-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #6b6b6b;
    margin-bottom: 0.5rem;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.2rem;
    color: #f0ece0;
    border-bottom: 1px solid #2a2a2a;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}

.stButton>button {
    background: #f0ece0;
    color: #0d0d0d;
    border: none;
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 0.6rem 1.5rem;
    transition: all 0.2s;
}
.stButton>button:hover {
    background: #b8f5a0;
    transform: translateY(-1px);
}

.stButton>button[kind="secondary"] {
    background: transparent;
    color: #6b6b6b;
    border: 1px solid #2a2a2a;
}

[data-testid="stSidebar"] {
    background: #111111;
    border-right: 1px solid #2a2a2a;
}

.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div>select,
.stDateInput>div>div>input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #f0ece0 !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
}

.stDataFrame {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}

/* Progress bar */
.progress-container {
    background: #1a1a1a;
    border-radius: 100px;
    height: 8px;
    margin: 0.5rem 0;
    overflow: hidden;
}
.progress-bar {
    height: 100%;
    border-radius: 100px;
    transition: width 0.5s ease;
}

.tag {
    display: inline-block;
    background: #2a2a2a;
    border-radius: 100px;
    padding: 0.2rem 0.8rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #6b6b6b;
    margin: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Database ────────────────────────────────────────────────────────────────
DB_PATH = "budget.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            label TEXT,
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fixed_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS daily_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT,
            note TEXT,
            date TEXT NOT NULL
        );
        """)

init_db()

# ─── DB helpers ─────────────────────────────────────────────────────────────
def add_income(amount, label, d):
    with get_conn() as conn:
        conn.execute("INSERT INTO income (amount, label, date) VALUES (?,?,?)", (amount, label, str(d)))

def add_fixed_cost(name, amount):
    with get_conn() as conn:
        conn.execute("INSERT INTO fixed_costs (name, amount) VALUES (?,?)", (name, amount))

def delete_fixed_cost(fid):
    with get_conn() as conn:
        conn.execute("DELETE FROM fixed_costs WHERE id=?", (fid,))

def add_expense(amount, category, note, d):
    with get_conn() as conn:
        conn.execute("INSERT INTO daily_expenses (amount, category, note, date) VALUES (?,?,?,?)",
                     (amount, category, note, str(d)))

def delete_expense(eid):
    with get_conn() as conn:
        conn.execute("DELETE FROM daily_expenses WHERE id=?", (eid,))

def get_income_this_month():
    today = date.today()
    ym = today.strftime("%Y-%m")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM income WHERE date LIKE ?", (ym+"%",)
        ).fetchone()
    return row[0]

def get_fixed_costs():
    with get_conn() as conn:
        return conn.execute("SELECT id, name, amount FROM fixed_costs WHERE active=1").fetchall()

def get_expenses_this_month():
    today = date.today()
    ym = today.strftime("%Y-%m")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, amount, category, note, date FROM daily_expenses WHERE date LIKE ? ORDER BY date DESC",
            (ym+"%",)
        ).fetchall()
    return rows

def get_expense_sum_this_month():
    today = date.today()
    ym = today.strftime("%Y-%m")
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM daily_expenses WHERE date LIKE ?", (ym+"%",)
        ).fetchone()
    return row[0]

def get_income_history():
    with get_conn() as conn:
        return conn.execute("SELECT id, amount, label, date FROM income ORDER BY date DESC LIMIT 20").fetchall()

# ─── Calculations ────────────────────────────────────────────────────────────
def days_left_in_month():
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return last_day - today.day + 1

def compute_budget():
    income      = get_income_this_month()
    fixed_sum   = sum(r[2] for r in get_fixed_costs())
    spent       = get_expense_sum_this_month()
    remaining   = income - fixed_sum - spent
    days_left   = days_left_in_month()
    daily_limit = remaining / days_left if days_left > 0 else 0
    return {
        "income": income,
        "fixed": fixed_sum,
        "spent": spent,
        "remaining": remaining,
        "days_left": days_left,
        "daily_limit": daily_limit,
    }

CATEGORIES = ["🛒 Jedzenie", "🚗 Transport", "☕ Kawa/Rozrywka", "💊 Zdrowie", "🛍️ Zakupy", "📱 Subskrypcje", "🏠 Dom", "💡 Inne"]

# ─── Sidebar nav ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="main-header">💰</p>', unsafe_allow_html=True)
    st.markdown('<p class="main-header">Mój<br>Budżet</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Personal Finance</p>', unsafe_allow_html=True)
    st.divider()
    page = st.radio(
        "Nawigacja",
        ["📊 Dashboard", "➕ Dodaj przychód", "🔒 Koszty stałe", "💸 Dodaj wydatek", "📋 Historia"],
        label_visibility="collapsed",
    )

# ─── Pages ──────────────────────────────────────────────────────────────────

# ══════════════ DASHBOARD ═══════════════
if page == "📊 Dashboard":
    b = compute_budget()

    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{date.today().strftime("%B %Y").upper()} · {b["days_left"]} DNI DO KOŃCA MIESIĄCA</p>', unsafe_allow_html=True)

    # Daily limit — hero number
    color_cls = "positive" if b["daily_limit"] > 50 else ("warning" if b["daily_limit"] > 0 else "negative")
    st.markdown(f"""
    <div class="metric-card" style="text-align:center; padding: 2.5rem;">
        <div class="metric-label">Dziś możesz wydać</div>
        <div class="big-number {color_cls}">{b['daily_limit']:,.2f} zł</div>
        <div style="color:#6b6b6b; font-family:'Space Mono',monospace; font-size:0.75rem; margin-top:0.5rem;">
            na dzień przez następne {b['days_left']} dni
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Przychód</div>
            <div class="big-number positive" style="font-size:1.8rem;">{b['income']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Koszty stałe</div>
            <div class="big-number warning" style="font-size:1.8rem;">{b['fixed']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Wydano</div>
            <div class="big-number negative" style="font-size:1.8rem;">{b['spent']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)

    # Spending progress bar
    if b["income"] > 0:
        used_pct = min((b["fixed"] + b["spent"]) / b["income"] * 100, 100)
        bar_color = "#b8f5a0" if used_pct < 70 else ("#f5d78a" if used_pct < 90 else "#f5a0a0")
        st.markdown(f"""
        <div style="margin-top:1rem;">
            <div class="metric-label">Wykorzystano budżetu: {used_pct:.1f}%</div>
            <div class="progress-container">
                <div class="progress-bar" style="width:{used_pct}%; background:{bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Recent expenses table
    st.markdown('<div class="section-title">Ostatnie wydatki</div>', unsafe_allow_html=True)
    expenses = get_expenses_this_month()
    if expenses:
        df = pd.DataFrame(expenses, columns=["ID", "Kwota (zł)", "Kategoria", "Notatka", "Data"])
        df = df.drop(columns=["ID"]).head(10)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p style="color:#6b6b6b; font-family:Space Mono,monospace; font-size:0.8rem;">Brak wydatków w tym miesiącu.</p>', unsafe_allow_html=True)

# ══════════════ DODAJ PRZYCHÓD ═══════════════
elif page == "➕ Dodaj przychód":
    st.markdown('<h1 class="main-header">Przychód</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">DODAJ WYPŁATĘ LUB INNY PRZYCHÓD</p>', unsafe_allow_html=True)

    with st.form("income_form"):
        amount = st.number_input("Kwota (zł)", min_value=0.01, step=100.0, format="%.2f")
        label  = st.text_input("Opis (np. 'Wypłata lipiec')", value="Wypłata")
        d      = st.date_input("Data", value=date.today())
        if st.form_submit_button("✓ Zapisz przychód"):
            add_income(amount, label, d)
            st.success(f"Zapisano: +{amount:,.2f} zł")
            st.rerun()

    # Historia przychodów
    st.markdown('<div class="section-title">Historia przychodów</div>', unsafe_allow_html=True)
    history = get_income_history()
    if history:
        df = pd.DataFrame(history, columns=["ID", "Kwota (zł)", "Opis", "Data"]).drop(columns=["ID"])
        st.dataframe(df, use_container_width=True, hide_index=True)

# ══════════════ KOSZTY STAŁE ═══════════════
elif page == "🔒 Koszty stałe":
    st.markdown('<h1 class="main-header">Koszty<br>Stałe</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">CZYNSZ, RATY, SUBSKRYPCJE…</p>', unsafe_allow_html=True)

    costs = get_fixed_costs()
    total = sum(r[2] for r in costs)

    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Suma kosztów stałych / miesiąc</div>
        <div class="big-number warning" style="font-size:2rem;">{total:,.2f} zł</div>
    </div>""", unsafe_allow_html=True)

    if costs:
        st.markdown('<div class="section-title">Lista</div>', unsafe_allow_html=True)
        for fid, name, amount in costs:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{name}**")
            col2.write(f"`{amount:,.2f} zł`")
            if col3.button("🗑", key=f"del_fc_{fid}"):
                delete_fixed_cost(fid)
                st.rerun()

    st.markdown('<div class="section-title">Dodaj nowy</div>', unsafe_allow_html=True)
    with st.form("fc_form"):
        name   = st.text_input("Nazwa (np. 'Czynsz')")
        amount = st.number_input("Kwota (zł)", min_value=0.01, step=50.0, format="%.2f")
        if st.form_submit_button("✓ Dodaj koszt"):
            if name:
                add_fixed_cost(name, amount)
                st.success(f"Dodano: {name} – {amount:,.2f} zł/mies.")
                st.rerun()

# ══════════════ DODAJ WYDATEK ═══════════════
elif page == "💸 Dodaj wydatek":
    st.markdown('<h1 class="main-header">Wydatek</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">SZYBKI ZAPIS WYDATKU</p>', unsafe_allow_html=True)

    b = compute_budget()
    color_cls = "positive" if b["daily_limit"] > 50 else ("warning" if b["daily_limit"] > 0 else "negative")
    st.markdown(f"""<div class="metric-card" style="text-align:center;">
        <div class="metric-label">Pozostały limit dzienny</div>
        <div class="big-number {color_cls}" style="font-size:2.5rem;">{b['daily_limit']:,.2f} zł</div>
    </div>""", unsafe_allow_html=True)

    with st.form("expense_form"):
        amount   = st.number_input("Kwota (zł)", min_value=0.01, step=1.0, format="%.2f")
        category = st.selectbox("Kategoria", CATEGORIES)
        note     = st.text_input("Notatka (opcjonalnie)")
        d        = st.date_input("Data", value=date.today())
        if st.form_submit_button("✓ Zapisz wydatek"):
            add_expense(amount, category, note, d)
            new_limit = b["daily_limit"] - amount
            st.success(f"Zapisano {amount:,.2f} zł · pozostało dziś: {new_limit:,.2f} zł")
            st.rerun()

# ══════════════ HISTORIA ═══════════════
elif page == "📋 Historia":
    st.markdown('<h1 class="main-header">Historia</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">WSZYSTKIE WYDATKI W TYM MIESIĄCU</p>', unsafe_allow_html=True)

    expenses = get_expenses_this_month()
    if expenses:
        df = pd.DataFrame(expenses, columns=["ID", "Kwota (zł)", "Kategoria", "Notatka", "Data"])

        # Category summary
        st.markdown('<div class="section-title">Według kategorii</div>', unsafe_allow_html=True)
        cat_df = df.groupby("Kategoria")["Kwota (zł)"].sum().reset_index().sort_values("Kwota (zł)", ascending=False)
        st.bar_chart(cat_df.set_index("Kategoria"))

        st.markdown('<div class="section-title">Wszystkie wydatki</div>', unsafe_allow_html=True)
        # Delete UI
        for _, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
            c1.write(f"`{row['Kwota (zł)']:,.2f} zł`")
            c2.write(row['Kategoria'])
            c3.write(f"{row['Notatka']} · {row['Data']}")
            if c4.button("🗑", key=f"del_exp_{row['ID']}"):
                delete_expense(row['ID'])
                st.rerun()
    else:
        st.info("Brak wydatków w tym miesiącu. Dodaj pierwszy wydatek!")
