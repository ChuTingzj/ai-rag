from generate.citations import CitationValidator, parse_citations


def test_parse_citations():
    assert parse_citations("费用上限为 3000 元[E1]。详见[E2]") == {1, 2}


def test_ungrounded_refuses():
    validator = CitationValidator(strictness="strict")
    result = validator.validate("随便说一句无引用", evidence_count=2)
    assert result.refuse_reason == "UNGROUNDED"


def test_invalid_citation_index_refuses():
    validator = CitationValidator(strictness="strict")
    result = validator.validate("越界引用[E99]", evidence_count=2)
    assert result.refuse_reason == "UNGROUNDED"
