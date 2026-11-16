"""
Human calibration dataset (Microsoft & Apple ONLY).
Nike is strictly excluded to prevent evaluation data leakage.
Provides pairs of (prediction, ground_truth, human_expert_score)
to validate that the automated DiligenceScorer strongly correlates with human judgment.
"""

HUMAN_CALIBRATION_SAMPLES = [
    {
        "prediction": "No single customer accounted for more than 10% of Microsoft's revenue in fiscal years 2023, 2022, or 2021. [MSFT:S030]",
        "ground_truth": {
            "id": "MSFT_TR_01",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S030]"],
            "key_facts": ["No single customer accounted for more than 10% of revenue in fiscal years 2023, 2022, or 2021"]
        },
        "human_score": 1.00 # Perfect answer with exact citation
    },
    {
        "prediction": "Customer revenue is distributed across segments: Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. [MSFT:S003]",
        "ground_truth": {
            "id": "MSFT_TR_01",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S030]"],
            "key_facts": ["No single customer accounted for more than 10% of revenue in fiscal years 2023, 2022, or 2021"]
        },
        "human_score": 0.35 # Incomplete, misses 10% concentration threshold
    },
    {
        "prediction": "Microsoft gross margin was 69% ($146,052 million). The accounting estimate change extending server useful life from 4 to 6 years reduced depreciation by $3.7B. [MSFT:S006] [MSFT:S025] [MSFT:S026]",
        "ground_truth": {
            "id": "MSFT_TR_02",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S006]", "[MSFT:S025]", "[MSFT:S026]"],
            "key_facts": ["gross margin was $146,052 million or 69%", "useful life from four to six years", "decreased depreciation expense by $3.7 billion"]
        },
        "human_score": 0.98 # Complete breakdown with all citations
    },
    {
        "prediction": "Gross margin was 69% in fiscal year 2023 compared to 68% in 2022. [MSFT:S006]",
        "ground_truth": {
            "id": "MSFT_TR_02",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S006]", "[MSFT:S025]", "[MSFT:S026]"],
            "key_facts": ["gross margin was $146,052 million or 69%", "useful life from four to six years", "decreased depreciation expense by $3.7 billion"]
        },
        "human_score": 0.55 # Accurate percentage, but missed accounting depreciation change
    },
    {
        "prediction": "Services net sales grew 9.1% to an all-time record of $85,200 million. [AAPL:S013]",
        "ground_truth": {
            "id": "AAPL_TR_04",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S013]"],
            "key_facts": ["Services net sales grew 9.1%", "$85,200 million", "all-time record"]
        },
        "human_score": 1.00 # Exact match
    },
    {
        "prediction": "Apple services performed well across various digital content categories.",
        "ground_truth": {
            "id": "AAPL_TR_04",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S013]"],
            "key_facts": ["Services net sales grew 9.1%", "$85,200 million", "all-time record"]
        },
        "human_score": 0.15 # Vague, no numbers, missing citation
    },
    {
        "prediction": "Detailed customer breakdown is not available in the report. [AAPL:S001]",
        "ground_truth": {
            "id": "AAPL_TR_01",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S023]", "[AAPL:S024]"],
            "key_facts": ["No single customer accounted for more than 10% of net sales"]
        },
        "human_score": 0.10 # Evasive hedging when data exists
    },
    {
        "prediction": "Mac net sales dropped 26.9% to $29,357 million from $40,177 million in fiscal 2022 due to challenging market conditions. [AAPL:S010]",
        "ground_truth": {
            "id": "AAPL_TR_03",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S010]"],
            "key_facts": ["decreased 26.9% to $29,357 million", "challenging market conditions", "comparison to prior year M2 launches"]
        },
        "human_score": 0.90
    },
    {
        "prediction": "Apple outsourced manufacturing primarily in China, India, and Vietnam. [AAPL:S025]",
        "ground_truth": {
            "id": "AAPL_TR_05",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S025]"],
            "key_facts": ["outsourced partners", "located primarily in China, India, and Vietnam"]
        },
        "human_score": 0.95
    },
    {
        "prediction": "Capital expenditures were $31,900 million primarily to support cloud infrastructure. [MSFT:S028]",
        "ground_truth": {
            "id": "MSFT_TR_04",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S028]"],
            "key_facts": ["$31,900 million in capital expenditures", "compared to $23,886 million", "primarily to support cloud infrastructure demand"]
        },
        "human_score": 0.85
    },
    {
        "prediction": "Microsoft returned capital via buybacks and dividends. [MSFT:S001]",
        "ground_truth": {
            "id": "MSFT_TR_07",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S034]"],
            "key_facts": ["$22.2 billion through share repurchases", "$19.8 billion through dividends"]
        },
        "human_score": 0.20 # Cites wrong sentence [MSFT:S001], lacks dollar figures
    },
    {
        "prediction": "Apple repurchased $77,550 million of stock and paid $15,025 million in cash dividends. [AAPL:S031]",
        "ground_truth": {
            "id": "AAPL_TR_07",
            "company": "AAPL",
            "ground_truth_citations": ["[AAPL:S031]"],
            "key_facts": ["repurchased $77,550 million of common stock", "paid $15,025 million in cash dividends"]
        },
        "human_score": 1.00
    }
]
