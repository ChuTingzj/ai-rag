from retrieve.rrf import rrf_fuse


def test_rrf_prefers_overlap():
    a = ["d1", "d2", "d3"]
    b = ["d3", "d1", "d4"]
    fused = rrf_fuse([a, b], k=60)
    assert fused[0] == "d1" or fused[0] == "d3"
    assert set(fused[:2]) == {"d1", "d3"}
