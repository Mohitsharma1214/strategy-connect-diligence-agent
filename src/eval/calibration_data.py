"""
Human calibration dataset.
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
        "human_score": 1.00
    },
    {
        "prediction": "Customer revenue is distributed across segments: Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. [MSFT:S003]",
        "ground_truth": {
            "id": "MSFT_TR_01",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S030]"],
            "key_facts": ["No single customer accounted for more than 10% of revenue in fiscal years 2023, 2022, or 2021"]
        },
        "human_score": 0.35 # Incomplete, missed the 10% threshold disclosure
    },
    {
        "prediction": "Microsoft gross margin was 69% ($146,052 million). The accounting estimate change extending server useful life from 4 to 6 years reduced depreciation by $3.7B. [MSFT:S006] [MSFT:S025] [MSFT:S026]",
        "ground_truth": {
            "id": "MSFT_TR_02",
            "company": "MSFT",
            "ground_truth_citations": ["[MSFT:S006]", "[MSFT:S025]", "[MSFT:S026]"],
            "key_facts": ["gross margin was $146,052 million or 69%", "useful life from four to six years", "decreased depreciation expense by $3.7 billion"]
        },
        "human_score": 0.98
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
        "human_score": 1.00
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
        "human_score": 0.10 # Evasive hedging
    },
    {
        "prediction": "Foot Locker accounted for 6% of NIKE Brand revenues. No single customer accounted for 10% or more. [NKE:S021] [NKE:S022]",
        "ground_truth": {
            "id": "NKE_UN_01",
            "company": "NKE",
            "ground_truth_citations": ["[NKE:S021]", "[NKE:S022]"],
            "key_facts": ["Foot Locker accounted for approximately 6% of total NIKE Brand revenues", "No single customer accounted for 10% or more of consolidated revenues"]
        },
        "human_score": 0.95
    },
    {
        "prediction": "NIKE gross margin contracted 250 bps to 43.5% due to markdowns on excess inventory and freight costs. [NKE:S005] [NKE:S006]",
        "ground_truth": {
            "id": "NKE_UN_02",
            "company": "NKE",
            "ground_truth_citations": ["[NKE:S005]", "[NKE:S006]"],
            "key_facts": ["contracted 250 basis points to 43.5%", "higher markdowns to liquidate excess inventory", "elevated freight and logistics costs"]
        },
        "human_score": 0.95
    },
    {
        "prediction": "Inventories were flat at $8,454 million. [NKE:S023]",
        "ground_truth": {
            "id": "NKE_UN_04",
            "company": "NKE",
            "ground_truth_citations": ["[NKE:S023]"],
            "key_facts": ["inventories were $8,454 million", "flat compared to $8,420 million"]
        },
        "human_score": 0.90
    }
]
