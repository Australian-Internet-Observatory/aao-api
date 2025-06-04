mapping = [
    {
        "to": "version",
        "transform": 1
    },
    # Keep all .uuid fields
    {
        "from": "*.uuid",
        "to": "*.uuid",
    },
    # Keep all fields from the 'observer' object
    {
        "from": "observer.*",
        "to": "observer.*",
        "transform": "NULL_STRING_TO_NONE"
    },
    # Other fields
    {
        "from": "observation.observed_on_device_at",
        "to": "observation.observed_on_device_at",
    },
    {
        "from": "observation.submitted_from_device_at",
        "to": "observation.submitted_from_device_at",
    },
    {
        "from": "observation.platform",
        "to": "observation.platform",
    },
    {
        "from": "observation.ad_format",
        "to": "observation.ad_format",
    },
    {
        "from": "observation.keyframes.[i].observed_at",
        "to": "observation.keyframes.[i].observed_at",
    },
    {
        "from": "observation.keyframes.[i].ocr_data.[j].text",
        "to": "observation.keyframes.[i].ocr_data.[j].text",
    },
    {
        "from": "observation.keyframes.[i].ocr_data.[j].confidence",
        "to": "observation.keyframes.[i].ocr_data.[j].confidence",
    },
    {
        "from": "enrichment.ccl.advertiser_name_extractions.[i]",
        "to": "enrichment.ccl.advertiser_name_extractions.[i]",
    },
    {
        # "from": "enrichment.meta_adlibrary_scrape.candidates.[i].vendor",
        "to": "enrichment.ccl.scrapes.[0].vendor",
        "transform": "META_ADLIBRARY"
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.ad_archive_id",
        "to": "enrichment.ccl.scrapes.[0].response.[i].ad_archive_id",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.categories.[j]",
        "to": "enrichment.ccl.scrapes.[0].response.[i].categories.[j]",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.collation_id",
        "to": "enrichment.ccl.scrapes.[0].response.[i].collation_id",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.contains_digital_created_media",
        "to": "enrichment.ccl.scrapes.[0].response.[i].contains_digital_created_media",
    },
    # contains_sensitive_content
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.contains_sensitive_content",
        "to": "enrichment.ccl.scrapes.[0].response.[i].contains_sensitive_content",
    },
    # currency
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.currency",
        "to": "enrichment.ccl.scrapes.[0].response.[i].currency",
    },
    # end_date
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.end_date",
        "to": "enrichment.ccl.scrapes.[0].response.[i].end_date",
    },
    # entity_type
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.entity_type",
        "to": "enrichment.ccl.scrapes.[0].response.[i].entity_type",
    },
    # gated_type
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.gated_type",
        "to": "enrichment.ccl.scrapes.[0].response.[i].gated_type",
    },
    # has_user_reported
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.has_user_reported",
        "to": "enrichment.ccl.scrapes.[0].response.[i].has_user_reported",
    },
    # hidden_safety_data
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.hidden_safety_data",
        "to": "enrichment.ccl.scrapes.[0].response.[i].hidden_safety_data",
    },
    # impressions_with_index.impressions_text
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.impressions_with_index.impressions_text",
        "to": "enrichment.ccl.scrapes.[0].response.[i].impressions_text",
    },
    # is_profile_page
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.is_profile_page",
        "to": "enrichment.ccl.scrapes.[0].response.[i].is_profile_page",
    },
    # page_id
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.page_id",
        "to": "enrichment.ccl.scrapes.[0].response.[i].page_id",
    },
    # page_is_deleted
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.page_is_deleted",
        "to": "enrichment.ccl.scrapes.[0].response.[i].page_is_deleted",
    },
    # page_name
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.page_name",
        "to": "enrichment.ccl.scrapes.[0].response.[i].page_name",
    },
    # political_countries
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.political_countries.[j]",
        "to": "enrichment.ccl.scrapes.[0].response.[i].political_countries.[j]",
    },
    # publisher_platform
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.publisher_platform.[j]",
        "to": "enrichment.ccl.scrapes.[0].response.[i].publisher_platform.[j]",
    },
    # reach_estimate
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.reach_estimate",
        "to": "enrichment.ccl.scrapes.[0].response.[i].reach_estimate",
    },
    # spend
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.spend",
        "to": "enrichment.ccl.scrapes.[0].response.[i].spend",
    },
    # start_date
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.start_date",
        "to": "enrichment.ccl.scrapes.[0].response.[i].start_date",
    },
    # Snapshot fields
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.title",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.title",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.body.text",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.body",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.caption",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.caption",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cta_type",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cta_type",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.country_iso_code",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.country_iso_code",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.current_page_name",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.current_page_name",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.is_reshared",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.is_reshared",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.page_categories.[j]",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.page_categories.[j]",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.page_entity_type",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.page_entity_type",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.page_like_count",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.page_like_count",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.page_name",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.page_name",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.page_profile_uri",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.page_profile_uri",
    },
    # Cards
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].title",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].title",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].body",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].body",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].caption",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].caption",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].cta_type",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].cta_type",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].link_description",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].link_description",
    },
    {
        "from": "enrichment.meta_adlibrary_scrape.candidates.[i].data.snapshot.cards.[j].link_url",
        "to": "enrichment.ccl.scrapes.[0].response.[i].snapshot.cards.[j].link_url",
    },
    # Wild cards
]
