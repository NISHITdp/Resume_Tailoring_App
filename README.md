# Resume Tailor — Nishit Mistry

A two-tab Streamlit app that tailors your master Jake's-template resumes to specific job descriptions using Claude Sonnet 4.5.

- **Data Scientist tab** → uses `templates/ds_master.tex`
- **Data Engineer tab** → uses `templates/de_master.tex`

Workflow per application: paste JD → click Generate → copy LaTeX → paste into Overleaf → download PDF.

---

## 1. One-time setup

### Install Python (if you don't have it)
Check: `python3 --version` (need 3.9+)

### Clone or download this folder, then in terminal:

```bash
cd resume_app
python3 -m venv venv
source venv/bin/activate          # Mac/Linux
# OR on Windows:  venv\Scripts\activate

pip install -r requirements.txt
```

### Get your Anthropic API key
1. Go to https://console.anthropic.com
2. Sign up / log in
3. Add credit ($5–10 to start)
4. Create an API key (Settings → API Keys → Create)
5. Copy `.env.example` to `.env` and paste your key:

```bash
cp .env.example .env
# then edit .env and replace the placeholder with your real key
```

Alternatively, you can paste the API key directly into the sidebar each session (it's not saved, so you'd retype every launch).

---

## 2. Run the app

```bash
source venv/bin/activate    # if not already active
streamlit run app.py
```

Browser opens at `http://localhost:8501`. Pick a tab, paste a JD, click Generate.

---

## 3. Cost

- **Per tailored resume:** ~$0.05 (Sonnet 4.5, ~3K input + ~3K output tokens)
- **60 apps/day:** ~$3/day, ~$90/month
- Cheaper than ChatGPT Plus ($20/mo) only if you're under ~400 apps/month. Above that, API > ChatGPT Plus on quality + reliability anyway.

---

## 4. What the app outputs

For each generated resume:

1. **Tailoring Notes** — top 5 JD keywords surfaced, gaps you don't meet, sponsorship flag, verdict (apply or skip)
2. **Tailored LaTeX code** — full file, copy into Overleaf, compile, download PDF
3. **Download .tex button** — saves the LaTeX as a file for offline compile

---

## 5. Editing the master resumes

If you update your DS or DE base resume content, edit:
- `templates/ds_master.tex`
- `templates/de_master.tex`

The app loads these fresh on every run, so changes take effect immediately on the next Generate click.

---

## 6. Deploying later (Streamlit Cloud)

When you want web access from anywhere:

1. Push this folder to a GitHub repo (private — `.env` is gitignored, won't leak)
2. Go to https://share.streamlit.io
3. Connect GitHub, pick the repo, set main file = `app.py`
4. In Streamlit Cloud → Settings → Secrets, add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-xxx..."
   ```
5. Deploy. Free tier handles personal usage fine.

---

## 7. Tailoring rules baked into the prompt

The prompt enforces:
- No fabrication — only rephrase/reorder existing content
- All 4 jobs and both projects preserved
- One-page output (master is pre-calibrated)
- Bolding preserved + JD keywords newly bolded
- Honest GAPS section so you know talking points before applying

If output drifts from these rules, edit `build_prompt()` in `app.py`.
