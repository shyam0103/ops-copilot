# app/agents/graph.py
from typing import TypedDict, List, Optional, Literal, Dict, Any

from langgraph.graph import StateGraph, END

from app.core.llm_client import LLMClient
from app.core.rag import search
from app.core.db import SessionLocal
from app.models.db_models import Ticket

llm_client = LLMClient()


class GraphState(TypedDict, total=False):
    # Input
    user_message: str
    conversation: List[Dict[str, str]]  # chat history: [{role, content}, ...]
    user_id: Optional[int]  # 🔒 USER ID FOR MULTI-TENANCY

    # Planner output
    plan_intent: Literal[
        "knowledge_query",
        "create_ticket",
        "chitchat",
        "list_tickets",
        "update_ticket",
    ]
    use_rag: bool
    create_ticket: bool
    ticket_title: Optional[str]
    ticket_description: Optional[str]
    severity: Optional[str]

    # For update_ticket intent
    target_ticket_id: Optional[int]
    new_status: Optional[str]
    new_severity: Optional[str]

    # RAG
    context_blocks: List[str]

    # Answer
    answer: str

    # Ticket (result of create/update)
    ticket_id: Optional[int]

    # per-turn trace of what each node did
    trace: List[Dict[str, Any]]


# Trace helper function
def _append_trace(
    state: GraphState,
    node: str,
    description: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    trace = list(state.get("trace") or [])
    entry: Dict[str, Any] = {"node": node, "description": description}
    if extra:
        entry.update(extra)
    trace.append(entry)
    state["trace"] = trace


# ---------- TOOLS ----------


def build_ticket_list_answer(user_message: str, user_id: int) -> str:
    """
    🔒 Tool-style function: reads tickets from DB (USER-SCOPED) and returns a text summary.
    """
    db = SessionLocal()
    try:
        tickets = (
            db.query(Ticket)
            .filter(Ticket.user_id == user_id)  # 🔒 USER ISOLATION
            .order_by(Ticket.created_at.desc())
            .limit(20)
            .all()
        )
    finally:
        db.close()

    if not tickets:
        return (
            "You have no tickets in the system. "
            "You can create one by describing an issue or request."
        )

    lines = ["Here are your latest tickets:\n"]
    for t in tickets:
        lines.append(
            f"- #{t.id} | {t.status.upper()} | {t.severity.upper()} | {t.title}"
        )

    lines.append(
        "\nYou can ask me things like:\n"
        "- 'Show only open tickets'\n"
        "- 'Show critical tickets'\n"
        "- 'Close ticket #3'\n"
        "- 'Reopen ticket 2 as medium severity'\n"
        "(Filters and advanced updates can be added later.)"
    )

    return "\n".join(lines)


def update_ticket_tool(state: GraphState) -> str:
    """
    🔒 Tool-style function: update a ticket's status/severity (USER-SCOPED).
    """
    ticket_id = state.get("target_ticket_id")
    new_status = (state.get("new_status") or "").lower() or None
    new_severity = (state.get("new_severity") or "").lower() or None
    user_id = state.get("user_id")

    if ticket_id is None:
        return (
            "I couldn't determine which ticket to update. "
            "Please specify the ticket number, e.g. 'Close ticket #3'."
        )

    db = SessionLocal()
    try:
        # 🔒 Only allow updating user's own tickets
        ticket = (
            db.query(Ticket)
            .filter(Ticket.id == ticket_id, Ticket.user_id == user_id)
            .first()
        )
        
        if not ticket:
            return f"Ticket #{ticket_id} was not found or does not belong to you."

        changes = []
        if new_status:
            ticket.status = new_status
            changes.append(f"status → {new_status.upper()}")
        if new_severity:
            ticket.severity = new_severity
            changes.append(f"severity → {new_severity.upper()}")

        if not changes:
            return (
                f"I found ticket #{ticket_id}, but no new status or severity was "
                "provided to update."
            )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        state["ticket_id"] = ticket.id

        changes_str = ", ".join(changes)
        return (
            f"Updated ticket #{ticket.id}: {changes_str}.\n"
            f"Title: {ticket.title}"
        )
    finally:
        db.close()


# ---------- NODES ----------


def planner_node(state: GraphState) -> GraphState:
    """Decide intent + ticket info using LLM (planner)."""
    user_message = state["user_message"]

    system_prompt = (
        "You are the Planner for OpsCopilot, a generic operations assistant used by any organization.\n"
        "Your job is to classify the user's message into an intent and decide what actions to take.\n\n"
        "INTENTS:\n"
        "- 'knowledge_query': The user is asking a question about policies, procedures, documents, or how to do something.\n"
        "- 'create_ticket': The user is reporting an issue, request, complaint, bug, incident, or task that should be tracked.\n"
        "- 'list_tickets': The user is asking to see existing tickets (e.g., 'show my open issues', 'list all tickets').\n"
        "- 'update_ticket': The user wants to change a ticket's status or severity (e.g., 'close ticket 3', 'mark ticket 2 critical').\n"
        "- 'chitchat': The user is just greeting or chatting casually.\n\n"
        "Decide also:\n"
        "- whether to use RAG (document search) for this message.\n"
        "- if a ticket should be created, suggest a title, description, and severity.\n"
        "- for update_ticket, identify:\n"
        "    - 'ticket_id': the numeric ticket id from the message (if any),\n"
        "    - 'new_status': the new status (e.g. 'open', 'closed', 'in_progress'),\n"
        "    - 'new_severity': the new severity ('low', 'medium', 'high', 'critical').\n\n"
        "Return ONLY a valid JSON object with the following keys:\n"
        "{\n"
        '  "intent": "knowledge_query" | "create_ticket" | "list_tickets" | "update_ticket" | "chitchat",\n'
        '  "use_rag": true or false,\n'
        '  "create_ticket": true or false,\n'
        '  "ticket_title": string or null,\n'
        '  "ticket_description": string or null,\n'
        '  "severity": "low" | "medium" | "high" | "critical",\n'
        '  "ticket_id": number or null,\n'
        '  "new_status": string or null,\n'
        '  "new_severity": string or null\n'
        "}\n"
        "Do not include any explanation, only JSON."
    )

    # Build messages with memory
    messages = [{"role": "system", "content": system_prompt}]
    for msg in state.get("conversation", []):
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    raw = llm_client.chat(messages)

    import json

    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            json_str = raw[start : end + 1]
        else:
            json_str = raw

        data = json.loads(json_str)
        intent = data.get("intent", "knowledge_query")
        use_rag = bool(data.get("use_rag", True))
        create_ticket = bool(data.get("create_ticket", False))
        ticket_title = data.get("ticket_title")
        ticket_description = data.get("ticket_description")
        severity = data.get("severity", "medium")
        target_ticket_id = data.get("ticket_id")
        new_status = data.get("new_status")
        new_severity = data.get("new_severity")

        # Ensure ticket_id is int if present
        if target_ticket_id is not None:
            try:
                target_ticket_id = int(target_ticket_id)
            except Exception:
                target_ticket_id = None
    except Exception:
        intent = "knowledge_query"
        use_rag = True
        create_ticket = False
        ticket_title = None
        ticket_description = None
        severity = "medium"
        target_ticket_id = None
        new_status = None
        new_severity = None

    state.update(
        {
            "plan_intent": intent,
            "use_rag": use_rag,
            "create_ticket": create_ticket,
            "ticket_title": ticket_title,
            "ticket_description": ticket_description,
            "severity": severity,
            "target_ticket_id": target_ticket_id,
            "new_status": new_status,
            "new_severity": new_severity,
        }
    )

    # Log planner decision
    ticket_action = None
    if intent == "create_ticket" and create_ticket:
        ticket_action = "create"
    elif intent == "update_ticket":
        ticket_action = "update"
    elif intent == "list_tickets":
        ticket_action = "list"

    _append_trace(
        state,
        "planner",
        f"Intent={intent}, use_rag={use_rag}, ticket_action={ticket_action or 'none'}",
    )
    
    return state


def rag_node(state: GraphState) -> GraphState:
    """🔒 Retrieve relevant document chunks if use_rag is True (USER-SCOPED)."""
    intent = state.get("plan_intent")
    user_id = state.get("user_id")

    # For list_tickets and update_ticket, we do NOT need RAG at all.
    if intent in ("list_tickets", "update_ticket"):
        state["context_blocks"] = []
        _append_trace(
            state,
            "rag",
            "Skipped RAG: intent does not require document search.",
        )
        return state

    if not state.get("use_rag", True):
        state["context_blocks"] = []
        _append_trace(
            state,
            "rag",
            "Skipped RAG: planner decided not to use document search.",
        )
        return state

    query = state["user_message"]

    # --- DEBUG: see what RAG is actually returning ---
    print("\n===== RAG DEBUG =====")
    print("Query:", repr(query))
    print(f"User ID: {user_id}")

    # 🔒 Pass user_id to search for isolation
    rag_results = search(query, user_id=user_id)
    context_blocks: List[str] = []

    if rag_results and rag_results.get("documents"):
        docs_list = rag_results["documents"]
        metas_list = rag_results["metadatas"]

        print("Num result groups:", len(docs_list))

        for group_idx, (docs, metas) in enumerate(zip(docs_list, metas_list)):
            print(f"  Group {group_idx}: {len(docs)} docs")
            for text, info in zip(docs, metas):
                page = info.get("page", "unknown")
                doc_id = info.get("document_id", "unknown")
                snippet = (text or "").replace("\n", " ")[:200]
                print(f"    [doc_id={doc_id}, page={page}] snippet: {snippet!r}")

                context_blocks.append(f"[Document {doc_id} | Page {page}] {text}")
    else:
        print("RAG returned no documents")

    print("===== END RAG DEBUG =====\n")

    state["context_blocks"] = context_blocks
    
    # Log retrieved chunks
    num_chunks = len(context_blocks)
    doc_ids: set[Any] = set()
    if rag_results and rag_results.get("metadatas"):
        for metas in rag_results["metadatas"]:
            for m in metas:
                doc_id = m.get("document_id")
                if doc_id is not None:
                    try:
                        doc_ids.add(int(doc_id))
                    except (ValueError, TypeError):
                        pass

    _append_trace(
        state,
        "rag",
        f"Retrieved {num_chunks} chunks from {len(doc_ids)} documents",
        {"doc_ids": list(doc_ids) or None},
    )

    return state


def answer_node(state: GraphState) -> GraphState:
    """
    Generate the main assistant answer.
    - For list_tickets: use the ticket list tool, no LLM.
    - For update_ticket: use the update tool, no LLM.
    - Otherwise: use LLM with or without RAG context.
    Also updates conversation memory.
    """
    intent = state.get("plan_intent", "knowledge_query")
    query = state["user_message"]
    user_id = state.get("user_id")

    # list_tickets → tool only
    if intent == "list_tickets":
        answer = build_ticket_list_answer(query, user_id)
        state["answer"] = answer

        _append_trace(state, "tickets", "Listed tickets for the user.")

        conversation = state.get("conversation", []).copy()
        conversation.append({"role": "user", "content": query})
        conversation.append({"role": "assistant", "content": answer})
        state["conversation"] = conversation

        return state

    # update_ticket → tool only
    if intent == "update_ticket":
        answer = update_ticket_tool(state)
        state["answer"] = answer

        _append_trace(
            state,
            "tickets",
            f"Updated ticket: {state.get('ticket_id') or state.get('target_ticket_id')}",
        )

        conversation = state.get("conversation", []).copy()
        conversation.append({"role": "user", "content": query})
        conversation.append({"role": "assistant", "content": answer})
        state["conversation"] = conversation

        return state

    # Normal path: knowledge_query / create_ticket / chitchat
    context_blocks = state.get("context_blocks") or []

    if context_blocks:
        context_text = "\n\n".join(context_blocks)
        system_prompt = (
            "You are OpsCopilot, a generic operations assistant. "
            "You are given document context from internal company documents. "
            "Your job is to read this context and answer the user's question by "
            "summarizing and combining any relevant information you find.\n\n"
            "RULES:\n"
            "- Assume the document context is relevant to the question.\n"
            "- If the context contains anything related to the question, you MUST "
            "use it to construct the best possible answer.\n"
            "- Base your answer ONLY on the document context; do not invent facts.\n"
            "- Do NOT say 'I don't know based on the uploaded documents'.\n"
            "- Only if there is truly no related information at all, say: "
            "'The uploaded documents do not mention this topic.'\n\n"
            "=== DOCUMENT CONTEXT ===\n"
            f"{context_text}\n"
            "=== END CONTEXT ==="
        )
    else:
        system_prompt = (
            "You are OpsCopilot, a generic operations assistant for any organization. "
            "There is no document context, so answer based on general best practices. "
            "Be helpful, but if you genuinely don't know, say so honestly."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in state.get("conversation", []):
        messages.append(msg)
    messages.append({"role": "user", "content": query})

    answer = llm_client.chat(messages)
    state["answer"] = answer

    _append_trace(
        state,
        "answer",
        "Answered using RAG context" if context_blocks else "Answered without RAG context",
    )

    # Update conversation memory
    conversation = state.get("conversation", []).copy()
    conversation.append({"role": "user", "content": query})
    conversation.append({"role": "assistant", "content": answer})
    state["conversation"] = conversation

    return state


def ticket_node(state: GraphState) -> GraphState:
    """🔒 Create a ticket in DB if plan says so (USER-SCOPED)."""
    if not (state.get("plan_intent") == "create_ticket" and state.get("create_ticket")):
        return state

    user_message = state["user_message"]
    answer = state.get("answer", "")
    user_id = state.get("user_id")

    title = state.get("ticket_title") or f"Issue: {user_message[:60]}"
    description = state.get("ticket_description") or (
        f"User message: {user_message}\n\nAssistant answer:\n{answer}"
    )
    severity = state.get("severity") or "medium"

    db = SessionLocal()
    ticket_id = None
    try:
        # 🔒 Create ticket with user_id
        ticket = Ticket(
            title=title,
            description=description,
            status="open",
            severity=severity,
            user_id=user_id  # 🔒 USER ISOLATION
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        ticket_id = ticket.id
        state["ticket_id"] = ticket_id
    finally:
        db.close()

    _append_trace(state, "tickets", f"Created new ticket #{ticket_id}")

    return state


# ---------- GRAPH DEFINITION ----------


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("planner", planner_node)
    g.add_node("rag", rag_node)
    g.add_node("answer", answer_node)
    g.add_node("ticket", ticket_node)

    g.set_entry_point("planner")
    g.add_edge("planner", "rag")
    g.add_edge("rag", "answer")
    g.add_edge("answer", "ticket")
    g.add_edge("ticket", END)

    return g.compile()


compiled_graph = build_graph()


def run_ops_graph(initial_state: GraphState) -> GraphState:
    """Run the graph and return final state (including updated conversation)."""
    # Initialize trace list in initial state before running
    initial_state["trace"] = []
    final_state = compiled_graph.invoke(initial_state)
    return final_state