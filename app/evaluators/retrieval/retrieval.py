from __future__ import annotations

import re
import math
from typing import List, Dict, Any, Optional, Set

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class TestQuestion(BaseModel):
    id: str = Field(...)
    question: str = Field(...)
    keywords: List[str] = Field(default_factory=list)


class RetrievalMetrics(BaseModel):
    hit: float
    mrr: float
    ndcg: float
    retrieved_count: int
    relevant_count: int
    keyword_coverage: float
    keywords_found: int
    total_keywords: int
    debug: Optional[Dict[str, Any]] = None


class RetrievalEvaluator:
    # too generic (but we still allow them to exist; we just won't count them strongly)
    GENERIC_KEYWORDS = {
        "redis", "data", "value", "values", "key", "keys", "command", "commands",
        "list", "hash", "set", "string", "sorted", "zset", "stream", "streams",
        "db", "database", "cache", "caching", "ttl", "memory",
    }

    def __init__(
            self,
            min_keyword_hits: int = 2,
            min_expected_overlap: int = 2,  # backward compatibility, unused
            min_question_overlap: int = 2,
            include_debug: bool = False,
    ):
        self.min_keyword_hits = min_keyword_hits
        self.min_question_overlap = min_question_overlap
        self.include_debug = include_debug

    def evaluate(self, test_question: TestQuestion, retrieved_chunks: List[Document]) -> RetrievalMetrics:
        docs = retrieved_chunks or []
        signals = self._build_signals(test_question)

        relevances = [1 if self._is_relevant(d.page_content or "", signals) else 0 for d in docs]

        hit = 1.0 if any(relevances) else 0.0
        mrr = self._mrr(relevances)
        ndcg = self._ndcg(relevances)

        keywords_found = self._keywords_found(signals["keywords_for_coverage"], docs)
        total_keywords = len(signals["keywords_for_coverage"])
        keyword_coverage = (keywords_found / total_keywords * 100.0) if total_keywords > 0 else 0.0

        debug = None
        if self.include_debug:
            debug = {
                "effective_keywords_used_for_relevance": signals["keywords_for_relevance"],
                "effective_keywords_used_for_coverage": signals["keywords_for_coverage"],
                "question_tokens_used": sorted(list(signals["question_tokens"]))[:50],
                "relevances": relevances,
                "keyword_hits_per_doc": [
                    self._keyword_hits(d.page_content or "", signals["keywords_for_relevance"]) for d in docs
                ],
                "question_overlap_per_doc": [
                    self._question_overlap(d.page_content or "", signals["question_tokens"]) for d in docs
                ],
                "doc_preview": [self._preview(d.page_content or "") for d in docs],
                "min_keyword_hits": self.min_keyword_hits,
                "min_question_overlap": self.min_question_overlap,
            }

        return RetrievalMetrics(
            hit=hit,
            mrr=mrr,
            ndcg=ndcg,
            retrieved_count=len(docs),
            relevant_count=int(sum(relevances)),
            keyword_coverage=keyword_coverage,
            keywords_found=keywords_found,
            total_keywords=total_keywords,
            debug=debug,
        )

    # ----------------------------
    # Signal building
    # ----------------------------
    def _build_signals(self, q: TestQuestion) -> Dict[str, Any]:
        # normalize keywords
        raw_keywords = [self._normalize(k) for k in (q.keywords or []) if self._normalize(k)]

        # for coverage: keep them all (even generic ones)
        keywords_for_coverage = raw_keywords

        # for relevance: drop generic ones (they are too easy / inflate relevance)
        keywords_for_relevance = [k for k in raw_keywords if k not in self.GENERIC_KEYWORDS]

        # question tokens fallback (helps basic/conceptual questions)
        # also removes super-short garbage tokens
        question_tokens = {t for t in self._tokens(q.question) if len(t) >= 3 and t not in self.GENERIC_KEYWORDS}

        return {
            "keywords_for_relevance": keywords_for_relevance,
            "keywords_for_coverage": keywords_for_coverage,
            "question_tokens": question_tokens,
        }

    # ----------------------------
    # Relevance logic
    # ----------------------------
    def _is_relevant(self, chunk_text: str, signals: Dict[str, Any]) -> bool:
        kw = signals["keywords_for_relevance"]
        hits = self._keyword_hits(chunk_text, kw)

        # dynamic threshold based on keyword count
        if len(kw) == 0:
            # no useful keywords left -> rely on question overlap
            return self._question_overlap(chunk_text, signals["question_tokens"]) >= self.min_question_overlap

        if len(kw) <= 2:
            # if we only have 1-2 strong keywords, a single match is enough
            if hits >= 1:
                return True
        else:
            if hits >= self.min_keyword_hits:
                return True

        # fallback: chunk still considered relevant if it overlaps question meaningfully
        if self._question_overlap(chunk_text, signals["question_tokens"]) >= self.min_question_overlap:
            return True

        return False

    def _explode_keyword(self, kw: str) -> List[str]:
        """
        Turns multi-word keyword like 'cache stampede' into ['cache','stampede'].
        Keeps single tokens as-is.
        """
        kw = self._normalize(kw)
        if not kw:
            return []
        parts = re.findall(r"[a-z0-9_\-]+", kw)
        return parts if len(parts) > 1 else [kw]

    def _keyword_hits(self, text: str, keywords: List[str]) -> int:
        if not keywords:
            return 0

        t = self._normalize(text)
        hits = 0

        for kw in keywords:
            tokens = self._explode_keyword(kw)
            if not tokens:
                continue

            # if any token from the keyword appears, count it as a hit (1 per keyword)
            for token in tokens:
                if re.search(rf"\b{re.escape(token)}\b", t):
                    hits += 1
                    break

        return hits

    def _question_overlap(self, text: str, question_tokens: Set[str]) -> int:
        if not question_tokens:
            return 0
        return len(set(self._tokens(text)) & question_tokens)

    # ----------------------------
    # Metrics
    # ----------------------------
    def _mrr(self, relevances: List[int]) -> float:
        for i, r in enumerate(relevances, start=1):
            if r == 1:
                return 1.0 / i
        return 0.0

    def _dcg(self, relevances: List[int]) -> float:
        return sum((rel / math.log2(i + 2)) for i, rel in enumerate(relevances) if rel > 0)

    def _ndcg(self, relevances: List[int]) -> float:
        if not relevances:
            return 0.0
        dcg = self._dcg(relevances)
        ideal = sorted(relevances, reverse=True)
        idcg = self._dcg(ideal)
        return dcg / idcg if idcg > 0 else 0.0

    def _keywords_found(self, keywords: List[str], docs: List[Document]) -> int:
        """
        Coverage metric: counts keywords that appear anywhere across retrieved docs.
        Uses token explosion, so 'cache stampede' matches if either word exists.
        """
        if not keywords:
            return 0

        text = " ".join((d.page_content or "") for d in docs).lower()

        found = 0
        for kw in keywords:
            tokens = self._explode_keyword(kw)
            if not tokens:
                continue
            if any(re.search(rf"\b{re.escape(tok)}\b", text) for tok in tokens):
                found += 1

        return found

    # ----------------------------
    # Helpers
    # ----------------------------
    def _normalize(self, s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").lower()).strip()

    def _tokens(self, s: str) -> List[str]:
        return re.findall(r"[a-z0-9_\-]+", self._normalize(s))

    def _preview(self, text: str, n: int = 160) -> str:
        t = re.sub(r"\s+", " ", (text or "")).strip()
        return t[:n] + ("..." if len(t) > n else "")
