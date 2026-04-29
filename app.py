"""
Resume Tailor App for Nishit Mistry — v3
Two pages: Data Scientist and Data Engineer

PHILOSOPHY (v3): The master .tex file is the SOURCE OF TRUTH.
Default behavior = output the master UNCHANGED.
Only modify content where the JD genuinely demands it.
Never restructure, never re-bold, never rewrite for stylistic reasons.
"""

import streamlit as st
import anthropic
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Resume Tailor — Nishit Mistry",
    page_icon="📄",
    layout="wide",
)

TEMPLATES_DIR = Path(__file__).parent / "templates"


# -----------------------------
# Default Prompt (v3 — minimal-edits philosophy)
# -----------------------------
DEFAULT_PROMPT_TEMPLATE = """You are tailoring a LaTeX resume to a specific job description. Your job is NOT to rewrite the resume. Your job is to make the SMALLEST POSSIBLE EDITS that improve JD alignment, and otherwise return the master resume EXACTLY as given.

================================
GOLDEN RULE
================================
The master resume below is the source of truth. Treat it as locked. Your default behavior is to OUTPUT THE MASTER UNCHANGED. Only deviate from the master when the JD demands a specific, surgical edit. If you are unsure whether to change something, DO NOT CHANGE IT.

================================
CANDIDATE CONTEXT
================================
Nishit Mistry — MS Information Management at UIUC. Targeting full-time {role_label} roles. International student, requires sponsorship.

================================
WHAT YOU MAY EDIT (and only when the JD genuinely demands it)
================================

1. TECH STACK LINE REORDERING — within each role's tech stack line (the line right after the company name with the | separator), you may reorder existing tools so JD-relevant tools appear earlier. You may NOT add tools, remove tools, or change tool names.

2. BULLET REORDERING — within a single role, you may reorder the existing bullets so the most JD-relevant bullet appears first. You may NOT delete bullets, add bullets, merge bullets, or split bullets.

3. SURGICAL WORD SWAPS — within a bullet, you may swap a generic word for a JD-specific synonym IF AND ONLY IF the swap is genuinely supported by the candidate's actual work. Examples of allowed swaps:
   - JD says "experimentation" → may rephrase "A/B Testing" as "experimentation/A/B Testing"
   - JD says "feature engineering" → may rephrase "scikit-learn pipeline" to surface "feature engineering pipeline"
   The original meaning, length, and metric must be preserved exactly. NEVER swap specific tools (do not change "GPT-4o" to "GenAI", do not change "scikit-learn" to "ML libraries").

4. SKILLS REORDERING — within each Technical Skills category, you may reorder existing items so JD-relevant tools appear first. You may NOT add or remove items.

================================
WHAT YOU MUST NEVER DO
================================

- NEVER add \\textbf{{}} bolding that isn't in the master. The master's bolding pattern is final.
- NEVER remove \\textbf{{}} bolding that is in the master.
- NEVER wrap \\section{{}} arguments in \\textbf{{}}. Section headers are styled by the template macro — do NOT touch them.
- NEVER wrap job titles or tech stack lines in \\textbf{{}}.
- NEVER add new tools, frameworks, or technologies that aren't in the master. Specifically:
  * Do NOT add Spark, PySpark, Hadoop, Kafka, "big data technologies" to a role unless they're already in that role's stack.
  * Do NOT replace "GPT-4o" with "GenAI" or "GenAI (GPT-4o)".
  * Do NOT add buzzwords like "production", "end-to-end", "scalable" if they aren't in the master bullet.
- NEVER change any number, percentage, or metric.
- NEVER make a bullet longer than its master version.
- NEVER add or remove any role, project, or skill category.
- NEVER modify the LaTeX preamble, packages, or macro definitions (everything before \\begin{{document}}).
- NEVER modify the contact information line.

================================
DECISION TEST FOR EVERY EDIT
================================
Before making ANY edit, ask yourself:
- "Does the JD specifically require this change?" → if no, do not edit.
- "Will the resume be measurably stronger for THIS specific role with this edit?" → if no, do not edit.
- "Am I changing this for cosmetic reasons or to 'sound better'?" → if yes, do not edit.

It is BETTER to return the master with zero edits than to make unnecessary changes. Most bullets should remain word-for-word identical to the master.

================================
OUTPUT FORMAT (STRICT)
================================
Return EXACTLY this — no other text before or after:

<LATEX>
[the complete .tex code, from \\documentclass to \\end{{document}}, ready to compile]
</LATEX>

<NOTES>
EDITS MADE:
[List each specific edit you made and why. If you made zero edits, write "No edits needed — master already aligns with JD." Be specific: "Reordered Sherwin tech stack to lead with Snowflake (JD emphasizes data warehousing)." NOT vague: "tailored Sherwin role."]

JD KEYWORDS ALREADY PRESENT IN MASTER (no edit needed):
[List 3-5 keywords from the JD that already appear in the master and where]

GAPS (JD requirements NOT met):
[honest list, or "None — strong alignment"]

SPONSORSHIP FLAG:
[Flag loud if JD says "no sponsorship", "must be authorized", "US citizen only". Otherwise: "Not flagged."]

VERDICT:
[Strong match / Worth a shot / Stretch / Skip] — [one sentence why]
</NOTES>

================================
MASTER LATEX RESUME (this is the locked source of truth)
================================
{master_tex}

================================
JOB DESCRIPTION
================================
{jd}
"""


# -----------------------------
# Helpers
# -----------------------------
def load_master_tex(role: str) -> str:
    filename = "ds_master.tex" if role == "ds" else "de_master.tex"
    path = TEMPLATES_DIR / filename
    if not path.exists():
        st.error(f"Master template not found: {path}")
        st.stop()
    return path.read_text(encoding="utf-8")


def build_prompt(template: str, master_tex: str, jd: str, role_label: str) -> str:
    return template.format(
        master_tex=master_tex,
        jd=jd,
        role_label=role_label,
    )


def call_claude(prompt: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def parse_response(response: str) -> tuple[str, str]:
    latex_code = ""
    notes = ""
    if "<LATEX>" in response and "</LATEX>" in response:
        latex_code = response.split("<LATEX>")[1].split("</LATEX>")[0].strip()
    if "<NOTES>" in response and "</NOTES>" in response:
        notes = response.split("<NOTES>")[1].split("</NOTES>")[0].strip()
    if not latex_code:
        latex_code = response.strip()
    return latex_code, notes


def diff_summary(master: str, tailored: str) -> str:
    """Quick sanity check: how many lines changed, did line count stay the same."""
    m_lines = master.splitlines()
    t_lines = tailored.splitlines()
    if len(m_lines) != len(t_lines):
        return f"⚠️ Line count changed: master={len(m_lines)} → tailored={len(t_lines)}. This may break formatting."
    changed = sum(1 for a, b in zip(m_lines, t_lines) if a != b)
    pct = (changed / len(m_lines)) * 100 if m_lines else 0
    return f"📊 Lines changed: {changed} of {len(m_lines)} ({pct:.0f}%). Lower is better — surgical edits should be < 15%."


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("⚙️ Setup")

# Load API key from (in priority order): Streamlit secrets (cloud) > .env (local) > manual input
def get_default_api_key() -> str:
    # 1. Streamlit Cloud secrets
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except (FileNotFoundError, Exception):
        pass
    # 2. Local .env or environment variable
    return os.getenv("ANTHROPIC_API_KEY", "")

env_key = get_default_api_key()
api_key = st.sidebar.text_input(
    "Anthropic API Key",
    value=env_key,
    type="password",
    help="Get one at console.anthropic.com",
)

if not api_key:
    st.sidebar.warning("⚠️ Add your API key to start tailoring.")

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Workflow:**\n"
    "1. Pick the role tab\n"
    "2. Paste the JD\n"
    "3. Click Generate\n"
    "4. Copy LaTeX → Overleaf → PDF"
)
st.sidebar.markdown("---")
st.sidebar.caption("v3 · Master = source of truth · Surgical edits only")


# -----------------------------
# Session state for editable prompt
# -----------------------------
if "prompt_template" not in st.session_state:
    st.session_state.prompt_template = DEFAULT_PROMPT_TEMPLATE


# -----------------------------
# Main UI
# -----------------------------
st.title("📄 Resume Tailor")
st.caption("v3 philosophy: master file is locked. Only surgical edits. Most bullets stay identical.")

with st.expander("🔧 View / Edit Prompt Template (advanced)", expanded=False):
    st.caption(
        "This prompt enforces minimal-edits behavior. Use `{master_tex}`, `{jd}`, `{role_label}` as placeholders. "
        "Edits persist for this session only."
    )
    col_p1, _ = st.columns([1, 5])
    with col_p1:
        if st.button("↺ Reset to Default", use_container_width=True):
            st.session_state.prompt_template = DEFAULT_PROMPT_TEMPLATE
            st.rerun()
    edited = st.text_area(
        "Prompt template",
        value=st.session_state.prompt_template,
        height=400,
        key="prompt_editor",
        label_visibility="collapsed",
    )
    if edited != st.session_state.prompt_template:
        st.session_state.prompt_template = edited

with st.expander("📄 View Master Templates (read-only)", expanded=False):
    col_t1, col_t2 = st.tabs(["DS Master", "DE Master"])
    with col_t1:
        st.code(load_master_tex("ds"), language="latex")
    with col_t2:
        st.code(load_master_tex("de"), language="latex")

st.markdown("---")

tab_ds, tab_de = st.tabs(["🔬 Data Scientist", "🔧 Data Engineer"])


def render_tab(role: str, role_label: str):
    st.subheader(f"Tailoring for: {role_label}")

    jd = st.text_area(
        "Paste the Job Description",
        height=300,
        key=f"jd_{role}",
        placeholder="Paste the full JD — title, responsibilities, qualifications.",
    )

    col_a, _ = st.columns([1, 4])
    with col_a:
        generate = st.button(
            "🚀 Generate Tailored Resume",
            key=f"btn_{role}",
            type="primary",
            use_container_width=True,
        )

    if generate:
        if not api_key:
            st.error("Add your API key in the sidebar first.")
            return
        if not jd.strip():
            st.error("Paste a JD first.")
            return

        with st.spinner(f"Tailoring {role_label} resume (surgical edits only)..."):
            try:
                master_tex = load_master_tex(role)
                prompt = build_prompt(
                    st.session_state.prompt_template,
                    master_tex,
                    jd,
                    role_label,
                )
                response = call_claude(prompt, api_key)
                latex_code, notes = parse_response(response)
            except anthropic.AuthenticationError:
                st.error("API key rejected. Check it in the sidebar.")
                return
            except anthropic.RateLimitError:
                st.error("Rate limit hit. Wait a minute.")
                return
            except Exception as e:
                st.error(f"Error: {e}")
                return

        st.success("Done.")

        # Sanity check: how much actually changed?
        diff_msg = diff_summary(master_tex, latex_code)
        st.info(diff_msg)

        if notes:
            with st.expander("📊 Edits, Keywords, Gaps, Verdict", expanded=True):
                st.markdown(notes)

        st.markdown("### Tailored LaTeX Code")
        st.code(latex_code, language="latex")
        st.download_button(
            "💾 Download .tex",
            data=latex_code,
            file_name=f"Nishit_Mistry_Resume_{role.upper()}_tailored.tex",
            mime="text/x-tex",
            key=f"dl_{role}",
        )


with tab_ds:
    render_tab("ds", "Data Scientist")

with tab_de:
    render_tab("de", "Data Engineer")
