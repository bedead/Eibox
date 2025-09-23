from typing import List, Optional

from app.core.logging import logger
from app.utils._text_helper import _to_text

from langchain_core.messages import BaseMessage


def should_update_memory(
    last_messages: List[BaseMessage],
    semantic_memory: Optional[dict] = None,
) -> bool:
    """
    Heuristic rules to decide if memory should update.
    Works on messages in format: [{"role": "user", "content": "Hi"}, ...]
    """
    # logger.debug(f"Evaluating memory update for messages: {last_messages}")

    # Extract role + text
    roles = [
        getattr(msg, "type", None) for msg in last_messages
    ]  # "human" | "ai" | "system"
    print(f"Roles in last messages: {roles}")
    contents = [_to_text(msg.content) for msg in last_messages]

    # 1. Token length heuristic
    total_tokens = sum(len(c.split()) for c in contents)
    if total_tokens > 200:  # adjust threshold
        return True

    # 2. Greeting / trivial filter
    trivial = {"hi", "hii", "hello", "thanks", "ok", "good morning"}
    if all(c.lower().strip() in trivial for c in contents if c.strip()):
        return False

    # # 3. Embedding similarity check (optional, pseudo-code)
    # try:
    #     from sentence_transformers import SentenceTransformer
    #     from sklearn.metrics.pairwise import cosine_similarity
    #
    #     model = SentenceTransformer("all-MiniLM-L6-v2")
    #
    #     context_text = " ".join(contents)
    #     ctx_emb = model.encode([context_text])
    #
    #     mem_text = json.dumps(semantic_memory or {})
    #     mem_emb = model.encode([mem_text])
    #
    #     sim = cosine_similarity(ctx_emb, mem_emb)[0][0]
    #     if sim < 0.7:  # threshold: lower → more different
    #         return True
    # except Exception as e:
    #     logger.warning(f"Embedding similarity check failed: {e}")

    # 4. Entity change detection (simple keyword-based for now)
    keywords = ["project", "job", "location", "works at", "email", "phone", "mails"]
    for c in contents:
        if any(kw in c.lower() for kw in keywords):
            return True

    return False
