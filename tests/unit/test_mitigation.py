"""Unit tests for Query Reformulator and Abstention Engine (Component 4.5 & 4.6).

Owned by: Sharad (System Architect & Integration Engineer)
"""

import pytest
from sentinel.mitigation.reformulator import QueryReformulator
from sentinel.mitigation.abstention import AbstentionEngine


def test_query_reformulator_strips_noise():
    noisy_query = "Please tell me what is the vacation policy in detail?"
    reformulated = QueryReformulator.reformulate(noisy_query)
    assert "the vacation policy" in reformulated.lower()
    assert "please tell me" not in reformulated.lower()


def test_abstention_engine_security_block():
    res = AbstentionEngine.security_block({"attack": "jailbreak"})
    assert res.abstain is True
    assert res.reason_code == "SECURITY_BLOCK"
    assert "security" in res.user_message.lower()


def test_abstention_engine_direct_contradiction():
    res = AbstentionEngine.direct_contradiction(
        violated_claim="Logs are deleted daily",
        source_evidence="policy.txt"
    )
    assert res.abstain is True
    assert res.reason_code == "DIRECT_CONTRADICTION"
    assert "contradicts" in res.user_message.lower()

