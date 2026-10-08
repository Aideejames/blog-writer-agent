// Change to your Render URL after deploying
const API_URL = "https://blog-writer-agent-api.onrender.com";

const form = document.getElementById("generate-form");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const resultBox = document.getElementById("result");
const postTitle = document.getElementById("post-title");
const postBody = document.getElementById("post-body");
const researchEl = document.getElementById("research");
const outlineEl = document.getElementById("outline");
const draftEl = document.getElementById("draft");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const topic = document.getElementById("topic").value.trim();
  const password = document.getElementById("password").value;

  if (!topic) return;

  // UI: loading state
  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-label").textContent = "Generating…";
  resultBox.classList.add("hidden");
  statusEl.classList.remove("hidden");
  statusEl.scrollIntoView({ behavior: "smooth", block: "nearest" });

  // Wake a cold Render backend
  try { await fetch(`${API_URL}/health`); } catch (_) {}

  try {
    const headers = { "Content-Type": "application/json" };
    if (password) headers["X-Demo-Password"] = password;

    const res = await fetch(`${API_URL}/generate`, {
      method: "POST",
      headers,
      body: JSON.stringify({ topic }),
    });

    if (res.status === 401) {
      statusEl.querySelector(".status-text").innerHTML =
        "❌ Incorrect password.";
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      statusEl.querySelector(".status-text").innerHTML =
        `❌ API error (${res.status}): ${err.detail || res.statusText}`;
      return;
    }

    const data = await res.json();

    // Render the result
    const { title, body } = splitTitle(data.final_post);
    postTitle.textContent = title || data.topic;
    postBody.innerHTML = markdownToHtml(body);
    researchEl.textContent = data.research;
    outlineEl.textContent = data.outline;
    draftEl.textContent = data.draft;

    statusEl.classList.add("hidden");
    resultBox.classList.remove("hidden");
    resultBox.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    console.error(err);
    statusEl.querySelector(".status-text").innerHTML =
      "❌ Could not reach the API. It may be waking up — try again in 30 seconds.";
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector(".btn-label").textContent = "Generate essay";
  }
});


/**
 * If the post starts with a markdown H1 (# Title), split it out.
 * Returns { title, body }.
 */
function splitTitle(md) {
  const trimmed = (md || "").trimStart();
  if (trimmed.startsWith("# ")) {
    const newline = trimmed.indexOf("\n");
    const title = newline === -1 ? trimmed.slice(2) : trimmed.slice(2, newline);
    const body = newline === -1 ? "" : trimmed.slice(newline + 1);
    return { title: title.trim(), body };
  }
  return { title: "", body: trimmed };
}


/**
 * Minimal Markdown → HTML. Handles headings, bold, italics, inline code.
 * No external deps.
 */
function markdownToHtml(md) {
  const escape = (s) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  const lines = escape(md || "").split("\n");
  const out = [];
  let para = [];

  const flush = () => {
    if (para.length) {
      out.push(`<p>${para.join(" ")}</p>`);
      para = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) { flush(); continue; }

    if (line.startsWith("### ")) { flush(); out.push(`<h3>${line.slice(4)}</h3>`); continue; }
    if (line.startsWith("## "))  { flush(); out.push(`<h2>${line.slice(3)}</h2>`); continue; }
    if (line.startsWith("# "))   { flush(); out.push(`<h1>${line.slice(2)}</h1>`); continue; }

    para.push(line);
  }
  flush();

  return out
    .join("\n")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*(?!\s)(.+?)(?<!\s)\*/g, "$1<em>$2</em>");
}