# ✍️ Blog Writer Agent

A multi-agent AI system that **researches, outlines, writes, and edits** a full blog post from a single topic input — built with **LangGraph**, **LangChain**, and **Google Gemini**, and deployed on **Streamlit Community Cloud**.

**🔗 Live demo:** https://blog-writer-agent-ky9myeyjsmjymbfcjowbe.streamlit.app

> 🔒 Password-protected demo — the API key is rate-limited.

---

## What it does

Enter a topic. The agent runs a four-stage pipeline and returns a polished blog post (~700–1000 words) in about 30–60 seconds.

| Stage | Agent | What it does |
|---|---|---|
| 1 | **Researcher** | Produces concise research notes — key concepts, angles, misconceptions, hook |
| 2 | **Outliner** | Builds a structured outline: title, thesis, 4–6 sections, bullets |
| 3 | **Writer** | Writes the full blog post from the outline in a conversational tone |
| 4 | **Editor** | Tightens prose, fixes grammar, improves transitions — without changing structure |

Each stage is a **node in a LangGraph `StateGraph`**, communicating through a shared `BlogState` dictionary.

---

## Why multi-agent?

A single LLM call asking for "a blog post about X" tends to produce generic, unstructured output. Splitting the task into narrow roles gives each stage a tight, well-defined brief — which produces significantly better results.

Two design principles used here:

- **Each node returns only what it changed.** LangGraph merges the partial update into the shared state. The researcher returns `{"research": text}`, not the whole state.
- **The editor's brief is deliberately narrow.** It polishes — it does not rewrite. Without that constraint, LLMs tend to discard the writer's work and introduce factual drift.

---

## Stack

| Layer | Tool |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM framework | [LangChain](https://github.com/langchain-ai/langchain) |
| Model | Google Gemini (`gemini-3-flash-preview`) |
| UI + hosting | [Streamlit Community Cloud](https://streamlit.io/cloud) |
| Secrets | `.env` locally · Streamlit secrets in production |

---

## Project structure

```
.
├── agent.py               CLI version (run from the terminal)
├── streamlit_app.py       Streamlit web app (with password gate)
├── requirements.txt
├── .env                   Local only — never commit
└── README.md
```

---

## Run locally

### 1. Clone and install

```bash
git clone https://github.com/Aideejames/blog-writer-agent.git
cd blog-writer-agent
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-3-flash-preview
```

Get a free Gemini API key at https://aistudio.google.com/app/apikey.

### 3a. Run the CLI version

```bash
python agent.py
```

It will prompt:

```
Enter a blog topic:
```

Type your topic, press Enter, wait ~30–60 seconds, and the final post is printed.

### 3b. Run the Streamlit version

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

> If you don't set a `password` secret locally, the password gate will fail. See "Deploying" below for how to add it.

---

## Deploying to Streamlit Community Cloud

1. Push the repo to GitHub.
2. Go to https://share.streamlit.io → **New app** → pick the repo.
3. Main file path: `streamlit_app.py`.
4. Click **Advanced settings** → **Secrets** → paste:

   ```toml
   GOOGLE_API_KEY = "your-gemini-api-key-here"
   GEMINI_MODEL = "gemini-3-flash-preview"
   password = "your-chosen-demo-password"
   ```

5. Click **Deploy**.

The password gate reads `st.secrets["password"]`, so only people you share the password with can run the app — protecting your API quota.

---

## How the password gate works

```python
def password_entered():
    if hmac.compare_digest(
        st.session_state.get("password", ""),
        st.secrets["password"],
    ):
        st.session_state["password_correct"] = True
        del st.session_state["password"]
```

- Uses `hmac.compare_digest` for **constant-time comparison** — prevents timing-based password guessing.
- The password lives in Streamlit secrets, **never in source code**.
- Once entered, `password_correct` is stored in session state — the user isn't asked again for the same session.

---

## Design notes

### Why not just one big prompt?

| Approach | Result |
|---|---|
| Single prompt: "Write a blog post about X" | Generic, unstructured, hard to iterate |
| **Multi-agent pipeline** | Better research, tighter structure, cleaner prose |

Each node is easier to debug, evaluate, and replace. Want a different writing style? Change only the `writer` prompt. Want fact-checking? Add a node between `researcher` and `outliner`.

### Why LangGraph (not plain function calls)?

- **One call runs the whole pipeline:** `blog_agent.invoke({"topic": ...})`
- Easy to add **loops, conditionals, parallel branches** later
- **Cleaner code** as the agent grows — nodes and edges are declarative
- Modern API: uses `StateGraph`, `START`, `END` — not the deprecated `set_entry_point()` / `set_finish_point()`

### Why check `isinstance(text, list)`?

Gemini sometimes returns content as a **list of parts** (text + signature + extras). The helper normalises it to a plain string so downstream nodes always receive a clean input.

---

## Possible enhancements

- **Real-time research** — add a Tavily or SerpAPI node before the outliner
- **Fact-checking node** — verify claims against sources before publishing
- **SEO optimisation** — add meta description, keywords, slug
- **Multi-language output** — detect or accept target language
- **Streaming UI** — stream tokens to the browser as each stage completes
- **History** — save generated posts to a database for review

---

## Requirements

```
streamlit
langchain
langchain-google-genai
langgraph
python-dotenv
```

Python 3.10+ recommended.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Idara Joshua James**  
GitHub: [@Aideejames](https://github.com/Aideejames)