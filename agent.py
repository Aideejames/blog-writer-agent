import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

# 1. Load environment
load_dotenv()

# 2. Initialize the LLM
llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL"))

# 3. Define the State
class BlogState(TypedDict):
    topic: str
    research: str
    outline: str
    draft: str
    final_post: str

# 4. The Researcher node
def researcher(state: BlogState) -> dict:
    topic = state["topic"]
    prompt = f"""You are a research assistant helping write a blog post.

Topic: {topic}

Produce concise research notes covering:
- Key concepts the reader must understand
- 3-5 interesting angles or subtopics
- Common misconceptions to address
- A compelling hook idea for the intro

Keep it under 300 words. Plain text, no markdown headers."""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return {"research": text}

# 5. The Outliner node
def outliner(state: BlogState) -> dict:
    topic = state["topic"]
    research = state["research"]
    prompt = f"""You are a content strategist. Build a detailed blog post outline.

Topic: {topic}

Research notes:
{research}

Produce an outline with:
- A working title
- A one-sentence thesis
- 4-6 section headings
- Under each heading, 2-4 bullet points of what to cover

Plain text, no markdown. Keep it tight and skimmable."""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return {"outline": text}

# 6. The Writer node
def writer(state: BlogState) -> dict:
    topic = state["topic"]
    outline = state["outline"]
    prompt = f"""You are a skilled blog writer. Write a full blog post based on the outline below.

Topic: {topic}

Outline:
{outline}

Guidelines:
- Conversational but authoritative tone
- Strong hook in the first 2 sentences
- Use the outline's section headings as the post's headings
- 700-1000 words
- End with a clear takeaway or call to action
- Write in complete paragraphs, not bullet points

Output only the blog post. No preamble, no meta-commentary."""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return {"draft": text}

# 7. The Editor node
def editor(state: BlogState) -> dict:
    topic = state["topic"]
    draft = state["draft"]
    prompt = f"""You are an expert editor. Polish the blog post draft below.

Topic: {topic}

Draft:
{draft}

Your job:
- Fix grammar, spelling, and punctuation
- Tighten wordy sentences (cut at least 10% of the length)
- Improve transitions between sections
- Keep the author's voice and all the original ideas
- Do not add new sections or change the structure
- Do not add commentary or notes

Output ONLY the polished blog post."""

    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content
    if isinstance(text, list):
        text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return {"final_post": text}

# 8. Build the graph
graph_builder = StateGraph(BlogState)

graph_builder.add_node("researcher", researcher)
graph_builder.add_node("outliner", outliner)
graph_builder.add_node("writer", writer)
graph_builder.add_node("editor", editor)

graph_builder.add_edge(START, "researcher")
graph_builder.add_edge("researcher", "outliner")
graph_builder.add_edge("outliner", "writer")
graph_builder.add_edge("writer", "editor")
graph_builder.add_edge("editor", END)

blog_agent = graph_builder.compile()

# 9. Run it
if __name__ == "__main__":
    topic = input("Enter a blog topic: ").strip()
    if not topic:
        topic = "AI agents for beginners"
        print(f"(no topic entered — using default: {topic})")

    print(f"\n>>> Running blog agent on: {topic}\n")
    print("This takes ~30-60 seconds. Sit tight...\n")

    result = blog_agent.invoke({
        "topic": topic,
        "research": "",
        "outline": "",
        "draft": "",
        "final_post": "",
    })

    print("=" * 60)
    print("FINAL POST")
    print("=" * 60)
    print(result["final_post"])