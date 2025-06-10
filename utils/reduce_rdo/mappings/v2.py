mapping = [
    {
        "from": "version",
        "to": "version",
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
        "from": "enrichment.ccl.scrapes.[i].vendor",
        "to": "enrichment.ccl.scrapes.[i].vendor",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].ad_archive_id",
        "to": "enrichment.ccl.scrapes.[h].response.[i].ad_archive_id",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].categories.[j]",
        "to": "enrichment.ccl.scrapes.[h].response.[i].categories.[j]",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].collation_id",
        "to": "enrichment.ccl.scrapes.[h].response.[i].collation_id",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].contains_digital_created_media",
        "to": "enrichment.ccl.scrapes.[h].response.[i].contains_digital_created_media",
    },
    # contains_sensitive_content
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].contains_sensitive_content",
        "to": "enrichment.ccl.scrapes.[h].response.[i].contains_sensitive_content",
    },
    # currency
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].currency",
        "to": "enrichment.ccl.scrapes.[h].response.[i].currency",
    },
    # end_date
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].end_date",
        "to": "enrichment.ccl.scrapes.[h].response.[i].end_date",
    },
    # entity_type
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].entity_type",
        "to": "enrichment.ccl.scrapes.[h].response.[i].entity_type",
    },
    # gated_type
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].gated_type",
        "to": "enrichment.ccl.scrapes.[h].response.[i].gated_type",
    },
    # has_user_reported
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].has_user_reported",
        "to": "enrichment.ccl.scrapes.[h].response.[i].has_user_reported",
    },
    # hidden_safety_data
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].hidden_safety_data",
        "to": "enrichment.ccl.scrapes.[h].response.[i].hidden_safety_data",
    },
    # impressions_with_index.impressions_text
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].impressions_with_index.impressions_text",
        "to": "enrichment.ccl.scrapes.[h].response.[i].impressions_text",
    },
    # is_profile_page
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].is_profile_page",
        "to": "enrichment.ccl.scrapes.[h].response.[i].is_profile_page",
    },
    # page_id
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].page_id",
        "to": "enrichment.ccl.scrapes.[h].response.[i].page_id",
    },
    # page_is_deleted
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].page_is_deleted",
        "to": "enrichment.ccl.scrapes.[h].response.[i].page_is_deleted",
    },
    # page_name
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].page_name",
        "to": "enrichment.ccl.scrapes.[h].response.[i].page_name",
    },
    # political_countries
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].political_countries.[j]",
        "to": "enrichment.ccl.scrapes.[h].response.[i].political_countries.[j]",
    },
    # publisher_platform
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].publisher_platform.[j]",
        "to": "enrichment.ccl.scrapes.[h].response.[i].publisher_platform.[j]",
    },
    # reach_estimate
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].reach_estimate",
        "to": "enrichment.ccl.scrapes.[h].response.[i].reach_estimate",
    },
    # spend
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].spend",
        "to": "enrichment.ccl.scrapes.[h].response.[i].spend",
    },
    # start_date
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].start_date",
        "to": "enrichment.ccl.scrapes.[h].response.[i].start_date",
    },
    # Snapshot fields
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.title",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.title",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.body.text",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.body",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.caption",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.caption",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cta_type",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cta_type",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.country_iso_code",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.country_iso_code",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.current_page_name",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.current_page_name",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.is_reshared",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.is_reshared",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.page_categories.[j]",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.page_categories.[j]",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.page_entity_type",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.page_entity_type",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.page_like_count",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.page_like_count",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.page_name",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.page_name",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.page_profile_uri",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.page_profile_uri",
    },
    # Cards
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].title",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].title",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].body",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].body",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].caption",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].caption",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].cta_type",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].cta_type",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].link_description",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].link_description",
    },
    {
        "from": "enrichment.ccl.scrapes.[h].response.response_interpreted.json_raw.[i].snapshot.cards.[j].link_url",
        "to": "enrichment.ccl.scrapes.[h].response.[i].snapshot.cards.[j].link_url",
    },
    # Wild cards
]
