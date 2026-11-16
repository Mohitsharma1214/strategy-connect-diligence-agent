"""
Generates the investor diligence question suite (~42 questions).
Splits:
- train (learning set): 20 questions (10 MSFT, 10 AAPL)
- held_out (in-distribution test): 12 questions (6 MSFT, 6 AAPL)
- unseen (out-of-distribution test): 10 questions (10 NKE)
"""

import json
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

QUESTIONS = [
    # ==========================================
    # MICROSOFT (MSFT) - TRAIN (10 Questions)
    # ==========================================
    {
        "id": "MSFT_TR_01",
        "company": "MSFT",
        "split": "train",
        "category": "Customer Concentration",
        "question": "How concentrated is Microsoft's revenue among its top customers?",
        "reference_answer": "No single customer accounted for more than 10% of Microsoft's revenue in fiscal years 2023, 2022, or 2021.",
        "ground_truth_citations": ["[MSFT:S030]"],
        "key_facts": ["No single customer accounted for more than 10% of revenue in fiscal years 2023, 2022, or 2021"]
    },
    {
        "id": "MSFT_TR_02",
        "company": "MSFT",
        "split": "train",
        "category": "Gross Margin & Accounting",
        "question": "What was Microsoft's gross margin in fiscal year 2023, and what accounting estimate change significantly impacted it?",
        "reference_answer": "Gross margin was $146,052 million, or 69% of revenue, compared to 68% in fiscal 2022. It was favorably impacted by an accounting change effective July 1, 2022 extending server and network equipment useful lives from four to six years, which reduced depreciation expense by $3.7 billion (a 2 percentage point favorable impact).",
        "ground_truth_citations": ["[MSFT:S006]", "[MSFT:S025]", "[MSFT:S026]"],
        "key_facts": ["gross margin was $146,052 million or 69%", "useful life from four to six years", "decreased depreciation expense by $3.7 billion"]
    },
    {
        "id": "MSFT_TR_03",
        "company": "MSFT",
        "split": "train",
        "category": "Segment Performance",
        "question": "What drove growth in the Intelligent Cloud segment in fiscal year 2023?",
        "reference_answer": "Intelligent Cloud revenue grew 17% (21% in constant currency) to $87,907 million, driven by Azure and other cloud services revenue growth of 27% (31% in constant currency).",
        "ground_truth_citations": ["[MSFT:S014]", "[MSFT:S015]"],
        "key_facts": ["Intelligent Cloud revenue was $87,907 million", "17% growth (21% constant currency)", "Azure and other cloud services grew 27% (31% CC)"]
    },
    {
        "id": "MSFT_TR_04",
        "company": "MSFT",
        "split": "train",
        "category": "Capital Allocation & Capex",
        "question": "How much did Microsoft spend on capital expenditures in fiscal year 2023 and why?",
        "reference_answer": "Capital expenditures including assets acquired under finance leases were $31,900 million in fiscal year 2023, up from $23,886 million in fiscal year 2022, primarily to support cloud infrastructure demand.",
        "ground_truth_citations": ["[MSFT:S028]"],
        "key_facts": ["$31,900 million in capital expenditures", "compared to $23,886 million", "primarily to support cloud infrastructure demand"]
    },
    {
        "id": "MSFT_TR_05",
        "company": "MSFT",
        "split": "train",
        "category": "Segment Performance",
        "question": "Why did More Personal Computing revenue decline in fiscal year 2023?",
        "reference_answer": "More Personal Computing revenue decreased 9% (6% in constant currency) to $54,734 million, driven by a 25% drop in Windows OEM revenue and a 24% drop in Devices revenue due to PC market softness and channel inventory adjustments.",
        "ground_truth_citations": ["[MSFT:S017]", "[MSFT:S018]", "[MSFT:S019]"],
        "key_facts": ["decreased 9% to $54,734 million", "Windows OEM revenue decreased 25%", "Devices revenue decreased 24%", "PC market softness"]
    },
    {
        "id": "MSFT_TR_06",
        "company": "MSFT",
        "split": "train",
        "category": "R&D Investment",
        "question": "What was Microsoft's research and development expense in fiscal year 2023 as a percentage of revenue?",
        "reference_answer": "Research and development expenses were $27,195 million, representing 13% of revenue, an 11% increase from $24,512 million in fiscal year 2022.",
        "ground_truth_citations": ["[MSFT:S022]"],
        "key_facts": ["$27,195 million", "13% of revenue", "increase of 11%"]
    },
    {
        "id": "MSFT_TR_07",
        "company": "MSFT",
        "split": "train",
        "category": "Shareholder Returns",
        "question": "How much capital did Microsoft return to shareholders via buybacks and dividends in fiscal year 2023?",
        "reference_answer": "Microsoft returned $42.0 billion to shareholders, consisting of $22.2 billion in share repurchases and $19.8 billion in dividends.",
        "ground_truth_citations": ["[MSFT:S034]"],
        "key_facts": ["$22.2 billion through share repurchases", "$19.8 billion through dividends"]
    },
    {
        "id": "MSFT_TR_08",
        "company": "MSFT",
        "split": "train",
        "category": "Restructuring & Headcount",
        "question": "Did Microsoft execute any restructuring or workforce reductions in fiscal year 2023?",
        "reference_answer": "Yes, Microsoft announced a reduction of approximately 10,000 positions in January 2023, ending with approximately 221,000 employees as of June 30, 2023, and recognized $1.2 billion in severance and restructuring charges.",
        "ground_truth_citations": ["[MSFT:S036]", "[MSFT:S037]"],
        "key_facts": ["reduction of approximately 10,000 positions", "headcount was 221,000", "$1.2 billion severance charges"]
    },
    {
        "id": "MSFT_TR_09",
        "company": "MSFT",
        "split": "train",
        "category": "Macro & FX",
        "question": "What impact did foreign exchange rates have on Microsoft's fiscal year 2023 top-line revenue?",
        "reference_answer": "Foreign currency headwinds reduced total revenue growth by 4 percentage points; reported revenue grew 7% but constant currency revenue grew 11%.",
        "ground_truth_citations": ["[MSFT:S004]", "[MSFT:S005]", "[MSFT:S035]"],
        "key_facts": ["headwinds reduced total revenue growth by 4 percentage points", "reported growth 7%", "constant currency growth 11%"]
    },
    {
        "id": "MSFT_TR_10",
        "company": "MSFT",
        "split": "train",
        "category": "Revenue Backlog & RPO",
        "question": "What was Microsoft's commercial remaining performance obligation (RPO) at fiscal year-end 2023, and what portion will be recognized in the next year?",
        "reference_answer": "Commercial RPO was $224 billion as of June 30, 2023, with approximately 45% expected to be recognized over the next twelve months.",
        "ground_truth_citations": ["[MSFT:S031]"],
        "key_facts": ["commercial RPO was $224 billion", "approximately 45% recognized over next twelve months"]
    },

    # ==========================================
    # APPLE (AAPL) - TRAIN (10 Questions)
    # ==========================================
    {
        "id": "AAPL_TR_01",
        "company": "AAPL",
        "split": "train",
        "category": "Customer Concentration",
        "question": "How concentrated is Apple's net sales among its top customers?",
        "reference_answer": "No single customer accounted for more than 10% of net sales in fiscal 2023, 2022, or 2021, although cellular network carriers and wholesalers distribute significant volumes.",
        "ground_truth_citations": ["[AAPL:S023]", "[AAPL:S024]"],
        "key_facts": ["No single customer accounted for more than 10% of net sales", "cellular network carriers distribute significant volumes but none exceed 10%"]
    },
    {
        "id": "AAPL_TR_02",
        "company": "AAPL",
        "split": "train",
        "category": "Gross Margin & Profitability",
        "question": "How did Apple's total gross margin change in fiscal 2023, and what drove Products vs Services margins?",
        "reference_answer": "Total gross margin rose to 44.1% ($169,148 million) from 43.3% in fiscal 2022. Products gross margin expanded to 36.5% (from 36.3%) due to favorable product mix and lower component costs, while Services gross margin fell 90 basis points to 70.8% due to higher content costs.",
        "ground_truth_citations": ["[AAPL:S004]", "[AAPL:S014]", "[AAPL:S015]"],
        "key_facts": ["gross margin was 44.1% ($169,148 million)", "Products gross margin expanded to 36.5%", "Services gross margin fell to 70.8% due to higher content costs"]
    },
    {
        "id": "AAPL_TR_03",
        "company": "AAPL",
        "split": "train",
        "category": "Product Performance",
        "question": "Why did Mac net sales decline significantly in fiscal 2023?",
        "reference_answer": "Mac net sales dropped 26.9% to $29,357 million from $40,177 million in fiscal 2022, caused by challenging market conditions and tough comparisons against the prior year's M2 chip launches.",
        "ground_truth_citations": ["[AAPL:S010]"],
        "key_facts": ["decreased 26.9% to $29,357 million", "challenging market conditions", "comparison to prior year M2 launches"]
    },
    {
        "id": "AAPL_TR_04",
        "company": "AAPL",
        "split": "train",
        "category": "Services Segment",
        "question": "How did Apple's Services segment perform in fiscal 2023?",
        "reference_answer": "Services net sales grew 9.1% to an all-time record of $85,200 million, up from $78,129 million in fiscal 2022.",
        "ground_truth_citations": ["[AAPL:S013]"],
        "key_facts": ["Services net sales grew 9.1%", "$85,200 million", "all-time record"]
    },
    {
        "id": "AAPL_TR_05",
        "company": "AAPL",
        "split": "train",
        "category": "Supply Chain & Manufacturing",
        "question": "Where is Apple's manufacturing concentrated and who performs it?",
        "reference_answer": "Substantially all manufacturing is performed by outsourced partners located primarily in China, India, and Vietnam.",
        "ground_truth_citations": ["[AAPL:S025]"],
        "key_facts": ["outsourced partners", "located primarily in China, India, and Vietnam"]
    },
    {
        "id": "AAPL_TR_06",
        "company": "AAPL",
        "split": "train",
        "category": "Cash Flow & Capex",
        "question": "What was Apple's free cash flow and capital expenditure in fiscal 2023?",
        "reference_answer": "Operating cash flow was $110,543 million and capital expenditures for property, plant, and equipment were $9,959 million, resulting in free cash flow of $100,584 million.",
        "ground_truth_citations": ["[AAPL:S026]", "[AAPL:S027]", "[AAPL:S028]"],
        "key_facts": ["capital expenditures were $9,959 million", "operating cash flow was $110,543 million", "free cash flow was $100,584 million"]
    },
    {
        "id": "AAPL_TR_07",
        "company": "AAPL",
        "split": "train",
        "category": "Shareholder Returns",
        "question": "What was the breakdown of Apple's capital returns to shareholders in fiscal 2023?",
        "reference_answer": "Apple repurchased $77,550 million of common stock and paid $15,025 million in cash dividends, totaling over $92.5 billion in shareholder returns.",
        "ground_truth_citations": ["[AAPL:S031]"],
        "key_facts": ["repurchased $77,550 million of common stock", "paid $15,025 million in cash dividends"]
    },
    {
        "id": "AAPL_TR_08",
        "company": "AAPL",
        "split": "train",
        "category": "Balance Sheet & Debt",
        "question": "What was Apple's total debt position as of September 30, 2023?",
        "reference_answer": "Total term debt was $105,963 million and commercial paper outstanding was $5,985 million, against $162,149 million in total cash and marketable securities.",
        "ground_truth_citations": ["[AAPL:S029]", "[AAPL:S030]"],
        "key_facts": ["term debt was $105,963 million", "commercial paper was $5,985 million", "cash and marketable securities were $162,149 million"]
    },
    {
        "id": "AAPL_TR_09",
        "company": "AAPL",
        "split": "train",
        "category": "Geographic Performance",
        "question": "Which geographic region was the only one to show net sales growth for Apple in fiscal 2023?",
        "reference_answer": "Rest of Asia Pacific was the only region that grew, increasing 0.8% to $29,615 million, while Americas, Europe, Greater China, and Japan all declined.",
        "ground_truth_citations": ["[AAPL:S018]", "[AAPL:S019]", "[AAPL:S020]", "[AAPL:S021]", "[AAPL:S022]"],
        "key_facts": ["Rest of Asia Pacific grew 0.8% to $29,615 million", "all other regions declined"]
    },
    {
        "id": "AAPL_TR_10",
        "company": "AAPL",
        "split": "train",
        "category": "Commitments & Off-Balance Sheet",
        "question": "What were Apple's manufacturing purchase obligations and commitments as of fiscal 2023 year-end?",
        "reference_answer": "Manufacturing purchase obligations and other commitments totaled $41,403 million as of September 30, 2023.",
        "ground_truth_citations": ["[AAPL:S035]"],
        "key_facts": ["manufacturing purchase obligations totaled $41,403 million"]
    },

    # ==========================================
    # MICROSOFT (MSFT) - HELD-OUT (6 Questions)
    # ==========================================
    {
        "id": "MSFT_HO_01",
        "company": "MSFT",
        "split": "held_out",
        "category": "Geographic Mix",
        "question": "What was the breakdown between Microsoft's United States and International revenue in fiscal year 2023?",
        "reference_answer": "United States revenue was $106,744 million (50.4% of total revenue) and International revenue was $105,171 million (49.6% of total revenue).",
        "ground_truth_citations": ["[MSFT:S038]", "[MSFT:S039]"],
        "key_facts": ["United States revenue was $106,744 million (50.4%)", "International revenue was $105,171 million (49.6%)"]
    },
    {
        "id": "MSFT_HO_02",
        "company": "MSFT",
        "split": "held_out",
        "category": "Taxes & Effective Rate",
        "question": "Why did Microsoft's effective tax rate increase in fiscal year 2023 compared to fiscal 2022?",
        "reference_answer": "The effective tax rate increased to 19.0% from 13.1% in fiscal year 2022, driven primarily by lower tax benefits from IP transfers and foreign tax credits.",
        "ground_truth_citations": ["[MSFT:S040]"],
        "key_facts": ["tax rate was 19.0% compared to 13.1%", "driven by lower tax benefits from IP transfers and foreign tax credits"]
    },
    {
        "id": "MSFT_HO_03",
        "company": "MSFT",
        "split": "held_out",
        "category": "Segment Performance",
        "question": "How did Microsoft Dynamics and Dynamics 365 perform in fiscal year 2023?",
        "reference_answer": "Dynamics revenue grew 16% (21% in constant currency), driven by Dynamics 365 revenue growth of 24% (30% in constant currency).",
        "ground_truth_citations": ["[MSFT:S013]"],
        "key_facts": ["Dynamics grew 16% (21% CC)", "Dynamics 365 grew 24% (30% CC)"]
    },
    {
        "id": "MSFT_HO_04",
        "company": "MSFT",
        "split": "held_out",
        "category": "Balance Sheet & Liquidity",
        "question": "What was Microsoft's total debt and cash position as of June 30, 2023?",
        "reference_answer": "Microsoft had $111,262 million in cash, cash equivalents, and short-term investments, and total debt of $59,965 million.",
        "ground_truth_citations": ["[MSFT:S032]", "[MSFT:S033]"],
        "key_facts": ["cash and short-term investments totaled $111,262 million", "total debt was $59,965 million"]
    },
    {
        "id": "MSFT_HO_05",
        "company": "MSFT",
        "split": "held_out",
        "category": "Gaming & Hardware",
        "question": "How did Xbox hardware perform within Microsoft's gaming division in fiscal year 2023?",
        "reference_answer": "Gaming revenue declined 5% (2% in constant currency), driven by an 11% decline in Xbox hardware revenue.",
        "ground_truth_citations": ["[MSFT:S020]"],
        "key_facts": ["Gaming revenue decreased 5%", "Xbox hardware revenue decreased 11%"]
    },
    {
        "id": "MSFT_HO_06",
        "company": "MSFT",
        "split": "held_out",
        "category": "Operating Leverage",
        "question": "How did Sales & Marketing and G&A expenses change for Microsoft in fiscal year 2023?",
        "reference_answer": "Sales and marketing expenses rose 4% to $22,759 million, while General and administrative expenses fell 3% to $7,575 million.",
        "ground_truth_citations": ["[MSFT:S023]", "[MSFT:S024]"],
        "key_facts": ["Sales and marketing was $22,759 million (+4%)", "G&A was $7,575 million (-3%)"]
    },

    # ==========================================
    # APPLE (AAPL) - HELD-OUT (6 Questions)
    # ==========================================
    {
        "id": "AAPL_HO_01",
        "company": "AAPL",
        "split": "held_out",
        "category": "Share Count & EPS",
        "question": "Why did Apple's diluted EPS increase in fiscal 2023 even though net income declined?",
        "reference_answer": "Diluted earnings per share grew to $6.13 from $6.11 despite net income falling to $96,995 million from $99,803 million, because share repurchases ($77.55B) lowered the weighted-average share count.",
        "ground_truth_citations": ["[AAPL:S006]", "[AAPL:S007]", "[AAPL:S031]"],
        "key_facts": ["EPS increased to $6.13 from $6.11", "net income fell to $96,995 million", "share repurchases reduced outstanding shares"]
    },
    {
        "id": "AAPL_TR_HO_02",
        "company": "AAPL",
        "split": "held_out",
        "category": "iPhone Performance",
        "question": "What were iPhone net sales in fiscal 2023 and what share of total net sales did they represent?",
        "reference_answer": "iPhone net sales were $200,583 million in fiscal 2023, representing 52.3% of total net sales ($383,285 million), down 2.4% from $205,489 million in fiscal 2022.",
        "ground_truth_citations": ["[AAPL:S003]", "[AAPL:S009]"],
        "key_facts": ["iPhone sales were $200,583 million", "down 2.4%", "total sales were $383,285 million (approx 52%)"]
    },
    {
        "id": "AAPL_HO_03",
        "company": "AAPL",
        "split": "held_out",
        "category": "R&D Intensity",
        "question": "How did Apple's R&D expenditure grow in fiscal 2023 relative to revenue contraction?",
        "reference_answer": "R&D spending increased 14.0% to $29,915 million (7.8% of net sales), up from $26,251 million (6.7% of net sales) in fiscal 2022, expanding R&D intensity even as net sales contracted by 2.8%.",
        "ground_truth_citations": ["[AAPL:S003]", "[AAPL:S016]"],
        "key_facts": ["R&D expense was $29,915 million", "7.8% of net sales", "up from $26,251 million (6.7%)"]
    },
    {
        "id": "AAPL_HO_04",
        "company": "AAPL",
        "split": "held_out",
        "category": "FX Impact",
        "question": "What headwind did foreign exchange rates impose on Apple's net sales in fiscal 2023?",
        "reference_answer": "Foreign exchange headwinds negatively affected total net sales by approximately 370 basis points in fiscal 2023.",
        "ground_truth_citations": ["[AAPL:S032]"],
        "key_facts": ["foreign exchange headwinds negatively affected sales by 370 basis points"]
    },
    {
        "id": "AAPL_HO_05",
        "company": "AAPL",
        "split": "held_out",
        "category": "Geographic Performance",
        "question": "What were Apple's net sales in Greater China in fiscal 2023 and how did they compare to fiscal 2022?",
        "reference_answer": "Greater China net sales were $72,559 million in fiscal 2023, down 2.2% from $74,202 million in fiscal 2022.",
        "ground_truth_citations": ["[AAPL:S020]"],
        "key_facts": ["Greater China net sales were $72,559 million", "down 2.2% from $74,202 million"]
    },
    {
        "id": "AAPL_HO_06",
        "company": "AAPL",
        "split": "held_out",
        "category": "Workforce",
        "question": "What was Apple's total full-time headcount at the end of fiscal 2023?",
        "reference_answer": "Apple had approximately 161,000 full-time equivalent employees as of September 30, 2023.",
        "ground_truth_citations": ["[AAPL:S034]"],
        "key_facts": ["approximately 161,000 full-time equivalent employees"]
    },

    # ==========================================
    # NIKE (NKE) - UNSEEN COMPANY (10 Questions)
    # ==========================================
    {
        "id": "NKE_UN_01",
        "company": "NKE",
        "split": "unseen",
        "category": "Customer Concentration",
        "question": "How concentrated is NIKE's revenue among its largest wholesale customers?",
        "reference_answer": "During fiscal 2023, NIKE's largest customer, Foot Locker, Inc., accounted for approximately 6% of total NIKE Brand revenues. No single customer accounted for 10% or more of consolidated revenues in fiscal 2023, 2022, or 2021.",
        "ground_truth_citations": ["[NKE:S021]", "[NKE:S022]"],
        "key_facts": ["Foot Locker accounted for approximately 6% of total NIKE Brand revenues", "No single customer accounted for 10% or more of consolidated revenues"]
    },
    {
        "id": "NKE_UN_02",
        "company": "NKE",
        "split": "unseen",
        "category": "Gross Margin Drivers",
        "question": "Why did NIKE's gross margin contract by 250 basis points in fiscal 2023?",
        "reference_answer": "Gross margin declined 250 basis points to 43.5% from 46.0% in fiscal 2022, primarily driven by higher promotional markdowns to clear excess inventory, adverse foreign currency exchange rates, and elevated freight/logistics costs, offset partially by strategic pricing actions.",
        "ground_truth_citations": ["[NKE:S005]", "[NKE:S006]"],
        "key_facts": ["contracted 250 basis points to 43.5%", "higher markdowns to liquidate excess inventory", "unfavorable foreign exchange", "elevated freight and logistics costs"]
    },
    {
        "id": "NKE_UN_03",
        "company": "NKE",
        "split": "unseen",
        "category": "Direct vs Wholesale Channels",
        "question": "Compare the revenue growth of NIKE Direct versus Wholesale in fiscal 2023.",
        "reference_answer": "NIKE Direct revenues were $21,308 million, growing 14% (20% currency-neutral), led by 24% digital growth. Wholesale revenues were $27,400 million, growing 7% (14% currency-neutral).",
        "ground_truth_citations": ["[NKE:S011]", "[NKE:S012]"],
        "key_facts": ["NIKE Direct was $21,308 million (+14%, 20% CC)", "Wholesale was $27,400 million (+7%, 14% CC)", "digital growth of 24%"]
    },
    {
        "id": "NKE_UN_04",
        "company": "NKE",
        "split": "unseen",
        "category": "Inventory Management",
        "question": "What was NIKE's inventory level at fiscal year-end 2023 and how did it change from fiscal 2022?",
        "reference_answer": "Inventories were $8,454 million as of May 31, 2023, flat compared to $8,420 million as of May 31, 2022, reflecting normalization of supply chain transit times.",
        "ground_truth_citations": ["[NKE:S023]"],
        "key_facts": ["inventories were $8,454 million", "flat compared to $8,420 million", "supply chain normalized"]
    },
    {
        "id": "NKE_UN_05",
        "company": "NKE",
        "split": "unseen",
        "category": "Supply Chain & Manufacturing",
        "question": "Where is NIKE's footwear manufacturing geographically concentrated?",
        "reference_answer": "Footwear was manufactured by independent contract manufacturers in Vietnam (50%), Indonesia (27%), and China (18%).",
        "ground_truth_citations": ["[NKE:S030]"],
        "key_facts": ["Vietnam (50%)", "Indonesia (27%)", "China (18%)"]
    },
    {
        "id": "NKE_UN_06",
        "company": "NKE",
        "split": "unseen",
        "category": "Geographic Performance",
        "question": "Why did NIKE's Greater China revenue decline on a reported basis in fiscal 2023?",
        "reference_answer": "Greater China revenues declined 4% on a reported basis (though increased 4% currency-neutral) to $7,248 million, heavily affected by COVID-19 lockdowns in the first half of the fiscal year.",
        "ground_truth_citations": ["[NKE:S018]"],
        "key_facts": ["declined 4% on reported basis to $7,248 million", "grew 4% currency-neutral", "COVID-19 lockdowns"]
    },
    {
        "id": "NKE_UN_07",
        "company": "NKE",
        "split": "unseen",
        "category": "Cash Flow & Capital Allocation",
        "question": "What was NIKE's free cash flow in fiscal 2023, and how much did it return to shareholders?",
        "reference_answer": "Free cash flow was $4,935 million (operating cash flow of $5,841M less capex of $906M), up 11.4%. NIKE returned $6.8 billion to shareholders via $4,778 million in share buybacks and $2,023 million in dividends.",
        "ground_truth_citations": ["[NKE:S024]", "[NKE:S025]", "[NKE:S026]", "[NKE:S029]"],
        "key_facts": ["free cash flow was $4,935 million", "operating cash flow $5,841M and capex $906M", "share repurchases $4,778 million and dividends $2,023 million"]
    },
    {
        "id": "NKE_UN_08",
        "company": "NKE",
        "split": "unseen",
        "category": "Marketing & Demand Creation",
        "question": "How much did NIKE spend on demand creation in fiscal 2023 and what drove it?",
        "reference_answer": "Demand creation expense was $4,060 million, up 5% from $3,850 million in fiscal 2022, driven by advertising and sports marketing investments.",
        "ground_truth_citations": ["[NKE:S008]"],
        "key_facts": ["$4,060 million", "up 5% from $3,850 million", "advertising and sports marketing"]
    },
    {
        "id": "NKE_UN_09",
        "company": "NKE",
        "split": "unseen",
        "category": "Effective Tax Rate",
        "question": "Why did NIKE's effective tax rate increase significantly in fiscal 2023?",
        "reference_answer": "The effective tax rate jumped to 18.2% from 9.1% in fiscal 2022, primarily due to lower tax benefits from stock-based compensation and discrete items.",
        "ground_truth_citations": ["[NKE:S032]"],
        "key_facts": ["rate was 18.2% compared to 9.1%", "lower benefits from stock-based compensation and discrete items"]
    },
    {
        "id": "NKE_UN_10",
        "company": "NKE",
        "split": "unseen",
        "category": "Commitments & Endorsements",
        "question": "What were NIKE's total endorsements and promotional commitments as of fiscal 2023 year-end?",
        "reference_answer": "Total endorsements and promotional commitments amounted to $7,842 million as of May 31, 2023.",
        "ground_truth_citations": ["[NKE:S034]"],
        "key_facts": ["endorsements and promotional commitments amounted to $7,842 million"]
    }
]

def main():
    questions_file = os.path.join(DATA_DIR, "questions.json")
    with open(questions_file, "w") as f:
        json.dump(QUESTIONS, f, indent=2)
    print(f"Generated {len(QUESTIONS)} questions in {questions_file}")
    
    splits = {}
    for q in QUESTIONS:
        splits[q["split"]] = splits.get(q["split"], 0) + 1
    print("Splits count:", splits)

if __name__ == "__main__":
    main()
