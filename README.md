# 💰 Mój Budżet — Personal Finance App

Prosta aplikacja budżetowa zbudowana w Pythonie + Streamlit. Działa lokalnie i na Streamlit Cloud (za darmo).

---

## ✨ Co robi ta aplikacja?

- 📊 **Dashboard** — pokazuje ile możesz wydać **dzisiaj** (dzienny limit)
- ➕ **Przychody** — dodajesz wypłatę lub inne przychody
- 🔒 **Koszty stałe** — czynsz, raty, subskrypcje (odejmowane automatycznie)
- 💸 **Wydatki** — szybki zapis codziennych wydatków z kategorią
- 📋 **Historia** — przegląd i wykres kategorii za bieżący miesiąc

### Formuła działa tak:
```
Dzienny limit = (Przychód − Koszty stałe − Wydatki) ÷ Dni do końca miesiąca
```

---

## 🚀 Uruchomienie lokalne (5 minut)

### 1. Sklonuj repozytorium
```bash
git clone https://github.com/TWOJ_USERNAME/moj-budzet.git
cd moj-budzet
```

### 2. Utwórz wirtualne środowisko (opcjonalnie, ale zalecane)
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 4. Uruchom aplikację
```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie pod adresem: **http://localhost:8501**

Baza danych `budget.db` (SQLite) zostanie utworzona automatycznie w tym samym folderze.

---

## ☁️ Deploy na Streamlit Cloud (za darmo!)

> **Uwaga**: Streamlit Cloud nie zachowuje pliku `budget.db` między restartami. Dla wersji chmurowej dane będą kasowane przy każdym restarcie. Do użytku osobistego najlepiej uruchamiaj lokalnie.

1. Wejdź na [share.streamlit.io](https://share.streamlit.io)
2. Zaloguj się przez GitHub
3. Kliknij **"New app"**
4. Wskaż repozytorium i plik `app.py`
5. Kliknij **Deploy** — gotowe!

---

## 📁 Struktura projektu

```
moj-budzet/
├── app.py              # Cała aplikacja Streamlit
├── requirements.txt    # Zależności Pythona
├── README.md           # Ten plik
└── budget.db           # Baza danych SQLite (tworzona automatycznie)
```

---

## 🔧 Jak wgrać na GitHub (pierwszy raz)

```bash
# W folderze projektu:
git init
git add .
git commit -m "Initial commit: mój budżet app"

# Utwórz repo na github.com, potem:
git remote add origin https://github.com/TWOJ_USERNAME/moj-budzet.git
git branch -M main
git push -u origin main
```

---

## 🗺️ Możliwe ulepszenia w przyszłości

- [ ] Eksport do CSV / Excel
- [ ] Wykresy miesięczne (trend wydatków)
- [ ] Cele oszczędnościowe
- [ ] Powiadomienia (np. e-mail gdy przekroczysz limit)
- [ ] Planowanie budżetu na przyszłe miesiące
- [ ] Tryb multi-użytkownik (logowanie)

---

*Zbudowane z ❤️ dla siebie — bo najlepsza aplikacja to ta, z której naprawdę korzystasz.*
