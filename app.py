import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import calendar

# ─── Page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Mój Budżet",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #f5f3ef; color: #1a1a1a; }
.main-header {
    font-family: 'DM Sans', sans-serif;
    font-size: 2.4rem; font-weight: 800;
    letter-spacing: -2px; color: #1a1a1a; line-height: 1.1;
}
.sub-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem; color: #999;
    letter-spacing: 3px; text-transform: uppercase; margin-bottom: 1.5rem;
}
.big-number { font-family: 'DM Mono', monospace; font-size: 3rem; font-weight: 500; line-height: 1; }
.big-number.positive { color: #1a7a40; }
.big-number.warning  { color: #a05a00; }
.big-number.negative { color: #b0241c; }
.metric-card {
    background: #fff; border: 1px solid #e0ddd8;
    border-radius: 14px; padding: 1.4rem; margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.metric-label {
    font-family: 'DM Mono', monospace; font-size: 0.6rem;
    letter-spacing: 3px; text-transform: uppercase; color: #aaa; margin-bottom: 0.4rem;
}
.section-title {
    font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 1.05rem;
    color: #1a1a1a; border-bottom: 2px solid #e0ddd8;
    padding-bottom: 0.35rem; margin: 1.4rem 0 0.8rem 0;
}
.highlight-box {
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: 12px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;
}
.stButton>button {
    background: #1a1a1a; color: #f5f3ef; border: none;
    border-radius: 8px; font-family: 'DM Mono', monospace;
    font-size: 0.8rem; padding: 0.6rem 1.5rem; transition: all 0.15s;
}
.stButton>button:hover { background: #1a7a40; transform: translateY(-1px); }
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e0ddd8; }
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input {
    background: #fff !important; border: 1px solid #d0cdc8 !important;
    color: #1a1a1a !important; border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important; font-size: 0.9rem !important;
}
.progress-container { background: #e0ddd8; border-radius: 100px; height: 10px; margin: 0.5rem 0; overflow: hidden; }
.progress-bar { height: 100%; border-radius: 100px; transition: width 0.5s ease; }
</style>
""", unsafe_allow_html=True)

# ─── Database ─────────────────────────────────────────────────────
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
            date TEXT NOT NULL          -- data wpływu wypłaty
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

# ─── DB helpers ───────────────────────────────────────────────────
def add_income(amount, label, d):
    with get_conn() as conn:
        conn.execute("INSERT INTO income (amount, label, date) VALUES (?,?,?)",
                     (amount, label, str(d)))

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

def get_all_income():
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, amount, label, date FROM income ORDER BY date DESC"
        ).fetchall()

def get_fixed_costs():
    with get_conn() as conn:
        return conn.execute("SELECT id, name, amount FROM fixed_costs WHERE active=1").fetchall()

def get_expenses_in_period(start: date, end: date):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, amount, category, note, date FROM daily_expenses "
            "WHERE date >= ? AND date <= ? ORDER BY date DESC",
            (str(start), str(end))
        ).fetchall()

# ─── Okres budżetowy: od ostatniej wypłaty do następnej ──────────
def get_current_budget_period():
    """
    Zwraca (okres_start, okres_end, kwota_przychodu) na podstawie
    dwóch ostatnich wpisów przychodu — aktualny okres to:
      start = data ostatniej wypłaty
      end   = data następnej wypłaty - 1 dzień
              (jeśli następnej brak → ostatni dzień bieżącego miesiąca)
    """
    all_inc = get_all_income()
    today = date.today()

    if not all_inc:
        # brak danych — wróć do miesiąca kalendarzowego
        last_day = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, 1), date(today.year, today.month, last_day), 0.0

    # posortuj rosnąco po dacie
    sorted_inc = sorted(all_inc, key=lambda r: r[3])

    # znajdź ostatnią wypłatę <= dziś
    past = [r for r in sorted_inc if r[3] <= str(today)]
    future = [r for r in sorted_inc if r[3] > str(today)]

    if not past:
        # wszystkie wypłaty w przyszłości — okres od dziś do pierwszej
        start = today
        end_date = date.fromisoformat(future[0][3]) - timedelta(days=1)
        return start, end_date, 0.0

    last = past[-1]
    period_start = date.fromisoformat(last[3])
    income_amount = last[1]

    if future:
        period_end = date.fromisoformat(future[0][3]) - timedelta(days=1)
    else:
        # brak następnej wypłaty — koniec = +31 dni od ostatniej
        period_end = period_start + timedelta(days=30)

    return period_start, period_end, income_amount

def compute_budget(ref_date: date = None):
    if ref_date is None:
        ref_date = date.today()

    period_start, period_end, income = get_current_budget_period()
    fixed_sum = sum(r[2] for r in get_fixed_costs())
    expenses  = get_expenses_in_period(period_start, period_end)
    spent     = sum(r[1] for r in expenses)
    remaining = income - fixed_sum - spent

    # dni od ref_date do końca okresu (włącznie)
    days_left = max((period_end - ref_date).days + 1, 1)
    daily_limit = remaining / days_left

    total_days = max((period_end - period_start).days + 1, 1)

    return {
        "income": income,
        "fixed": fixed_sum,
        "spent": spent,
        "remaining": remaining,
        "days_left": days_left,
        "total_days": total_days,
        "daily_limit": daily_limit,
        "period_start": period_start,
        "period_end": period_end,
        "expenses": expenses,
    }

CATEGORIES = [
    "🛒 Jedzenie", "🚗 Transport", "☕ Kawa/Rozrywka",
    "💊 Zdrowie", "🛍️ Zakupy", "📱 Subskrypcje", "🏠 Dom", "💡 Inne"
]

# ─── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="main-header">💰 Mój<br>Budżet</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Personal Finance</p>', unsafe_allow_html=True)
    st.divider()
    page = st.radio(
        "Nawigacja",
        ["📊 Dashboard", "🔢 Kalkulator dnia", "➕ Dodaj przychód",
         "🔒 Koszty stałe", "💸 Dodaj wydatek", "📋 Historia"],
        label_visibility="collapsed",
    )

# ══════════════ DASHBOARD ════════════════════════════════════════
if page == "📊 Dashboard":
    b = compute_budget()

    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    period_label = (
        f"{b['period_start'].strftime('%-d %b')} → {b['period_end'].strftime('%-d %b %Y')}"
    )
    st.markdown(
        f'<p class="sub-header">OKRES: {period_label} · {b["days_left"]} DNI DO KOŃCA</p>',
        unsafe_allow_html=True
    )

    color_cls = (
        "positive" if b["daily_limit"] > 50
        else "warning" if b["daily_limit"] > 0
        else "negative"
    )
    st.markdown(f"""
    <div class="metric-card" style="text-align:center; padding:2.5rem;">
        <div class="metric-label">Dziś możesz wydać</div>
        <div class="big-number {color_cls}">{b['daily_limit']:,.2f} zł</div>
        <div style="color:#999; font-family:'DM Mono',monospace; font-size:0.75rem; margin-top:0.6rem;">
            {b['days_left']} dni do {b['period_end'].strftime('%-d %b')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Przychód (ostatnia wypłata)</div>
            <div class="big-number positive" style="font-size:1.7rem;">{b['income']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Koszty stałe</div>
            <div class="big-number warning" style="font-size:1.7rem;">{b['fixed']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Wydano w tym okresie</div>
            <div class="big-number negative" style="font-size:1.7rem;">{b['spent']:,.0f} zł</div>
        </div>""", unsafe_allow_html=True)

    if b["income"] > 0:
        used_pct = min((b["fixed"] + b["spent"]) / b["income"] * 100, 100)
        days_pct = (b["total_days"] - b["days_left"]) / b["total_days"] * 100
        bar_color = "#22c55e" if used_pct < 70 else "#f59e0b" if used_pct < 90 else "#ef4444"
        st.markdown(f"""
        <div style="margin-top:1rem;">
            <div class="metric-label">Budżet: {used_pct:.1f}% wydane · {days_pct:.0f}% okresu minęło</div>
            <div class="progress-container">
                <div class="progress-bar" style="width:{used_pct}%; background:{bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Ostatnie wydatki</div>', unsafe_allow_html=True)
    if b["expenses"]:
        df = pd.DataFrame(b["expenses"], columns=["ID", "Kwota (zł)", "Kategoria", "Notatka", "Data"])
        st.dataframe(df.drop(columns=["ID"]).head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Brak wydatków w tym okresie.")

# ══════════════ KALKULATOR DNIA ══════════════════════════════════
elif page == "🔢 Kalkulator dnia":
    st.markdown('<h1 class="main-header">Kalkulator<br>Dnia</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">ILE ZOSTAŁO NA WYBRANY DZIEŃ?</p>', unsafe_allow_html=True)

    b_today = compute_budget()

    st.markdown(f"""
    <div class="highlight-box">
        <div class="metric-label">Aktualny okres budżetowy</div>
        <div style="font-size:1.1rem; font-weight:700; color:#1a1a1a;">
            {b_today['period_start'].strftime('%-d %B')} → {b_today['period_end'].strftime('%-d %B %Y')}
        </div>
        <div style="color:#888; font-size:0.85rem; margin-top:0.3rem;">
            Łącznie {b_today['total_days']} dni · wypłata {b_today['income']:,.0f} zł
        </div>
    </div>
    """, unsafe_allow_html=True)

    chosen_date = st.date_input(
        "Wybierz dzień",
        value=date.today(),
        min_value=b_today["period_start"],
        max_value=b_today["period_end"],
    )

    b = compute_budget(ref_date=chosen_date)

    # ile wydano DO wybranego dnia (włącznie)
    expenses_to_date = get_expenses_in_period(b["period_start"], chosen_date)
    spent_to_date = sum(r[1] for r in expenses_to_date)
    remaining_to_date = b["income"] - b["fixed"] - spent_to_date
    days_left_from_chosen = max((b["period_end"] - chosen_date).days + 1, 1)
    daily_from_chosen = remaining_to_date / days_left_from_chosen

    color_cls = (
        "positive" if daily_from_chosen > 50
        else "warning" if daily_from_chosen > 0
        else "negative"
    )

    st.markdown(f"""
    <div class="metric-card" style="text-align:center; padding:2rem;">
        <div class="metric-label">Dzienny limit od {chosen_date.strftime('%-d %b')} do końca okresu</div>
        <div class="big-number {color_cls}">{daily_from_chosen:,.2f} zł / dzień</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Wydano do {chosen_date.strftime('%-d %b')}</div>
            <div class="big-number negative" style="font-size:1.6rem;">{spent_to_date:,.2f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Pozostało środków</div>
            <div class="big-number {'positive' if remaining_to_date >= 0 else 'negative'}" style="font-size:1.6rem;">{remaining_to_date:,.2f} zł</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">Dni do końca okresu</div>
            <div class="big-number" style="font-size:1.6rem; color:#1a1a1a;">{days_left_from_chosen}</div>
        </div>""", unsafe_allow_html=True)

    if expenses_to_date:
        st.markdown(f'<div class="section-title">Wydatki do {chosen_date.strftime("%-d %b")}</div>',
                    unsafe_allow_html=True)
        df = pd.DataFrame(expenses_to_date,
                          columns=["ID", "Kwota (zł)", "Kategoria", "Notatka", "Data"])
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

# ══════════════ DODAJ PRZYCHÓD ═══════════════════════════════════
elif page == "➕ Dodaj przychód":
    st.markdown('<h1 class="main-header">Przychód</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">DODAJ DATĘ I KWOTĘ WYPŁATY</p>', unsafe_allow_html=True)

    st.markdown("""
    <div class="highlight-box">
        <div class="metric-label">Jak to działa?</div>
        <div style="font-size:0.9rem; color:#1a1a1a; line-height:1.6;">
            Każdy wpis przychodu = <strong>jedna wypłata</strong>. Aplikacja automatycznie
            liczy okres od daty tej wypłaty do daty następnej. Nie musisz ustawiać
            stałego dnia miesiąca — każda wypłata może być w innym dniu.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("income_form"):
        amount = st.number_input("Kwota wypłaty (zł)", min_value=0.01, step=100.0, format="%.2f")
        label  = st.text_input("Opis", value="Wypłata")
        d      = st.date_input("Data wpływu", value=date.today())
        if st.form_submit_button("✓ Zapisz wypłatę"):
            add_income(amount, label, d)
            st.success(f"Zapisano: +{amount:,.2f} zł dnia {d.strftime('%-d %b %Y')} ✓")
            st.rerun()

    st.markdown('<div class="section-title">Historia wypłat</div>', unsafe_allow_html=True)
    all_inc = get_all_income()
    if all_inc:
        df = pd.DataFrame(all_inc, columns=["ID", "Kwota (zł)", "Opis", "Data"])
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)
    else:
        st.info("Brak zapisanych wypłat. Dodaj pierwszą!")

# ══════════════ KOSZTY STAŁE ═════════════════════════════════════
elif page == "🔒 Koszty stałe":
    st.markdown('<h1 class="main-header">Koszty<br>Stałe</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">CZYNSZ, RATY, SUBSKRYPCJE…</p>', unsafe_allow_html=True)

    costs = get_fixed_costs()
    total = sum(r[2] for r in costs)

    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Suma miesięczna</div>
        <div class="big-number warning" style="font-size:2rem;">{total:,.2f} zł / okres</div>
    </div>""", unsafe_allow_html=True)

    if costs:
        st.markdown('<div class="section-title">Lista</div>', unsafe_allow_html=True)
        for fid, name, amount in costs:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{name}**")
            col2.write(f"{amount:,.2f} zł")
            if col3.button("🗑", key=f"del_fc_{fid}"):
                delete_fixed_cost(fid)
                st.rerun()

    st.markdown('<div class="section-title">Dodaj nowy koszt</div>', unsafe_allow_html=True)
    with st.form("fc_form"):
        name   = st.text_input("Nazwa (np. Czynsz)")
        amount = st.number_input("Kwota (zł)", min_value=0.01, step=50.0, format="%.2f")
        if st.form_submit_button("✓ Dodaj"):
            if name:
                add_fixed_cost(name, amount)
                st.success(f"Dodano: {name} – {amount:,.2f} zł/okres")
                st.rerun()

# ══════════════ DODAJ WYDATEK ════════════════════════════════════
elif page == "💸 Dodaj wydatek":
    st.markdown('<h1 class="main-header">Wydatek</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">SZYBKI ZAPIS</p>', unsafe_allow_html=True)

    b = compute_budget()
    color_cls = (
        "positive" if b["daily_limit"] > 50
        else "warning" if b["daily_limit"] > 0
        else "negative"
    )
    st.markdown(f"""<div class="metric-card" style="text-align:center;">
        <div class="metric-label">Limit dzienny (zostało {b['days_left']} dni)</div>
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
            st.success(f"Zapisano {amount:,.2f} zł · nowy limit dzienny: {new_limit:,.2f} zł")
            st.rerun()

# ══════════════ HISTORIA ═════════════════════════════════════════
elif page == "📋 Historia":
    st.markdown('<h1 class="main-header">Historia</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">WYDATKI W BIEŻĄCYM OKRESIE</p>', unsafe_allow_html=True)

    b = compute_budget()
    expenses = b["expenses"]

    if expenses:
        df = pd.DataFrame(expenses, columns=["ID", "Kwota (zł)", "Kategoria", "Notatka", "Data"])

        st.markdown('<div class="section-title">Według kategorii</div>', unsafe_allow_html=True)
        cat_df = (
            df.groupby("Kategoria")["Kwota (zł)"]
            .sum().reset_index()
            .sort_values("Kwota (zł)", ascending=False)
        )
        st.bar_chart(cat_df.set_index("Kategoria"))

        st.markdown('<div class="section-title">Wszystkie wydatki</div>', unsafe_allow_html=True)
        for _, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 3, 1])
            c1.write(f"**{row['Kwota (zł)']:,.2f} zł**")
            c2.write(row["Kategoria"])
            c3.write(f"{row['Notatka']}  ·  {row['Data']}")
            if c4.button("🗑", key=f"del_exp_{row['ID']}"):
                delete_expense(row["ID"])
                st.rerun()
    else:
        st.info("Brak wydatków w bieżącym okresie budżetowym.")
