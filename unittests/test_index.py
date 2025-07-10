from utils.opensearch.rdo_open_search import AdWithRDO, RdoOpenSearch

opensearch = RdoOpenSearch(index='test-rdo-index')

def test_create_index_v2():
    v2_ad = AdWithRDO(
        observer_id="5447b2f8-1624-4925-b2f0-17e912e41e8a",
        timestamp=1745376769468,
        ad_id="778460ba-b9e2-4eb1-a3e3-07195fc8a8e1",
    )
    assert v2_ad.open_search_id == "5447b2f8-1624-4925-b2f0-17e912e41e8a.778460ba-b9e2-4eb1-a3e3-07195fc8a8e1"
    opensearch.put(v2_ad)
    assert opensearch.get(v2_ad.open_search_id) is not None
    
def test_create_index_v1():
    v1_ad = AdWithRDO(
        observer_id="f60b6e94-7625-4044-9153-1f70863f81d8",
        timestamp=1729569092202,
        ad_id="d14f1dc0-5685-49e5-83d9-c46e29139373",
    )
    assert v1_ad.open_search_id == "f60b6e94-7625-4044-9153-1f70863f81d8.d14f1dc0-5685-49e5-83d9-c46e29139373"
    opensearch.put(v1_ad)
    assert opensearch.get(v1_ad.open_search_id) is not None