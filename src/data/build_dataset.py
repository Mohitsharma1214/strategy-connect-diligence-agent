"""
Dataset builder for diligence agent.
Generates comprehensive 10-K sections for:
1. Microsoft FY2023 (Learning & Held-out)
2. Apple FY2023 (Learning & Held-out)
3. Nike FY2023 (Unseen Evaluation Company)

All filings are structured with unambiguous sentence and table cell IDs:
e.g. [MSFT:S01], [AAPL:T05_C02]
"""

import json
import os
import re

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
FILINGS_DIR = os.path.join(DATA_DIR, "filings")
os.makedirs(FILINGS_DIR, exist_ok=True)

MSFT_TEXT = """[MSFT:S001] Microsoft Corporation is a Washington corporation founded in 1975.
[MSFT:S002] We generate revenue by offering a wide range of services, including cloud-based solutions that provide customers with software, services, platforms, and content.
[MSFT:S003] Our three reportable segments are Productivity and Business Processes, Intelligent Cloud, and More Personal Computing.
[MSFT:S004] For fiscal year 2023, total revenue was $211,915 million, an increase of 7% compared to $198,270 million for fiscal year 2022.
[MSFT:S005] In constant currency, total revenue increased 11% year-over-year.
[MSFT:S006] Gross margin for fiscal year 2023 was $146,052 million, or 69% of revenue, compared to $135,620 million, or 68% of revenue, in fiscal year 2022.
[MSFT:S007] Operating income was $88,523 million, up 6% compared to $83,383 million in fiscal year 2022.
[MSFT:S008] Net income was $72,361 million, down slightly from $72,738 million in fiscal year 2022.
[MSFT:S009] Diluted earnings per share was $9.68 for fiscal year 2023 compared to $9.65 for fiscal year 2022.
[MSFT:S010] Productivity and Business Processes revenue was $69,274 million, an increase of 8% driven by Office 365 Commercial and LinkedIn.
[MSFT:S011] Office 365 Commercial revenue grew 13% (17% in constant currency), driven by seat growth and higher revenue per user.
[MSFT:S012] LinkedIn revenue increased 10% (14% in constant currency), driven by growth across Talent Solutions.
[MSFT:S013] Dynamics revenue grew 16% (21% in constant currency), driven by Dynamics 365 growth of 24% (30% in constant currency).
[MSFT:S014] Intelligent Cloud revenue was $87,907 million, an increase of 17% (21% in constant currency), driven by Azure and other cloud services.
[MSFT:S015] Azure and other cloud services revenue grew 27% (31% in constant currency), reflecting continued customer commitment to our platform.
[MSFT:S016] Server products revenue decreased 1% (increased 2% in constant currency), driven by hybrid solutions growth offset by licensing declines.
[MSFT:S017] More Personal Computing revenue was $54,734 million, a decrease of 9% (decreased 6% in constant currency), driven by declines in Windows OEM and Devices.
[MSFT:S018] Windows OEM revenue decreased 25% due to PC market softness following strong pandemic demand.
[MSFT:S019] Devices revenue decreased 24% as we experienced elevated customer channel inventory and PC market weakness.
[MSFT:S020] Gaming revenue decreased 5% (decreased 2% in constant currency), driven by decreases in Xbox hardware revenue of 11%.
[MSFT:S021] Search and news advertising revenue excluding traffic acquisition costs increased 5% (8% in constant currency).
[MSFT:S022] Research and development expenses were $27,195 million, or 13% of revenue, compared to $24,512 million in fiscal year 2022, representing an increase of 11%.
[MSFT:S023] General and administrative expenses were $7,575 million, a decrease of 3% compared to $7,825 million in fiscal year 2022.
[MSFT:S024] Sales and marketing expenses were $22,759 million, an increase of 4% compared to $21,825 million in fiscal year 2022.
[MSFT:S025] Effective July 1, 2022, we revised our estimated useful life of server and network equipment from four to six years.
[MSFT:S026] This accounting change in useful life decreased depreciation expense by $3.7 billion for fiscal year 2023, favorably impacting gross margin by 2 percentage points.
[MSFT:S027] Cash provided by operations was $87,582 million in fiscal year 2023, compared to $89,035 million in fiscal year 2022.
[MSFT:S028] Capital expenditures including assets acquired under finance leases were $31,900 million, compared to $23,886 million in fiscal year 2022, primarily to support cloud infrastructure demand.
[MSFT:S029] Free cash flow was $59,475 million in fiscal year 2023, compared to $65,149 million in fiscal year 2022.
[MSFT:S030] No single customer accounted for more than 10% of revenue in fiscal years 2023, 2022, or 2021.
[MSFT:S031] Commercial remaining performance obligations (RPO) were $224 billion as of June 30, 2023, of which approximately 45% will be recognized over the next twelve months.
[MSFT:S032] Cash, cash equivalents, and short-term investments totaled $111,262 million as of June 30, 2023.
[MSFT:S033] Total debt, including short-term and long-term notes and finance lease obligations, was $59,965 million as of June 30, 2023.
[MSFT:S034] During fiscal year 2023, we returned $22.2 billion to shareholders through share repurchases and $19.8 billion through dividends.
[MSFT:S035] Foreign currency headwinds reduced total revenue growth by 4 percentage points in fiscal year 2023.
[MSFT:S036] Headcount as of June 30, 2023 was approximately 221,000 employees, reflecting a reduction of approximately 10,000 positions announced in January 2023.
[MSFT:S037] Severance and related restructuring charges recognized in fiscal year 2023 were $1.2 billion.
[MSFT:S038] United States revenue was $106,744 million in fiscal year 2023, representing 50.4% of total revenue.
[MSFT:S039] International revenue was $105,171 million in fiscal year 2023, representing 49.6% of total revenue.
[MSFT:S040] The effective tax rate for fiscal year 2023 was 19.0% compared to 13.1% in fiscal year 2022, driven primarily by lower tax benefits from IP transfers and foreign tax credits.
"""

AAPL_TEXT = """[AAPL:S001] Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories, and sells a variety of related services.
[AAPL:S002] The Company's fiscal year is the 52- or 53-week period that ends on the last Saturday of September.
[AAPL:S003] Total net sales were $383,285 million in fiscal 2023, a decrease of 2.8% compared to $394,328 million in fiscal 2022.
[AAPL:S004] Total gross margin was $169,148 million, or 44.1% of net sales, in fiscal 2023, compared to $170,782 million, or 43.3% of net sales, in fiscal 2022.
[AAPL:S005] Operating income was $114,301 million in fiscal 2023, down 4.3% from $119,437 million in fiscal 2022.
[AAPL:S006] Net income was $96,995 million in fiscal 2023, compared to $99,803 million in fiscal 2022.
[AAPL:S007] Diluted earnings per share increased to $6.13 in fiscal 2023 from $6.11 in fiscal 2022, due to share repurchases reducing outstanding shares.
[AAPL:S008] Products net sales were $298,085 million in fiscal 2023, a decrease of 5.7% from $316,199 million in fiscal 2022.
[AAPL:S009] iPhone net sales were $200,583 million in fiscal 2023, down 2.4% compared to $205,489 million in fiscal 2022.
[AAPL:S010] Mac net sales were $29,357 million in fiscal 2023, a decrease of 26.9% compared to $40,177 million in fiscal 2022, due to challenging market conditions and comparison to prior year M2 launches.
[AAPL:S011] iPad net sales were $28,300 million in fiscal 2023, down 3.4% compared to $29,292 million in fiscal 2022.
[AAPL:S012] Wearables, Home and Accessories net sales were $39,845 million in fiscal 2023, down 3.4% compared to $41,241 million in fiscal 2022.
[AAPL:S013] Services net sales were $85,200 million in fiscal 2023, an increase of 9.1% compared to $78,129 million in fiscal 2022, reaching an all-time record.
[AAPL:S014] Services gross margin was 70.8% in fiscal 2023 compared to 71.7% in fiscal 2022, a decline of 90 basis points due to higher content costs.
[AAPL:S015] Products gross margin expanded to 36.5% in fiscal 2023 from 36.3% in fiscal 2022, driven by favorable product mix and lower component costs, partially offset by foreign exchange weakness.
[AAPL:S016] Research and development expense was $29,915 million, or 7.8% of net sales, compared to $26,251 million, or 6.7% of net sales, in fiscal 2022.
[AAPL:S017] Selling, general, and administrative expense was $24,932 million, or 6.5% of net sales, compared to $25,094 million in fiscal 2022.
[AAPL:S018] Americas net sales were $162,560 million in fiscal 2023, down 4.2% from $169,658 million in fiscal 2022.
[AAPL:S019] Europe net sales were $94,294 million in fiscal 2023, slightly down from $95,118 million in fiscal 2022.
[AAPL:S020] Greater China net sales were $72,559 million in fiscal 2023, down 2.2% from $74,202 million in fiscal 2022.
[AAPL:S021] Japan net sales were $24,257 million in fiscal 2023, down 6.6% from $25,977 million in fiscal 2022.
[AAPL:S022] Rest of Asia Pacific net sales were $29,615 million in fiscal 2023, up 0.8% from $29,372 million in fiscal 2022.
[AAPL:S023] No single customer accounted for more than 10% of net sales in fiscal 2023, 2022, or 2021.
[AAPL:S024] Cellular network carriers and wholesalers distribute significant volumes, but none represented 10% or more of net sales.
[AAPL:S025] Substantially all manufacturing is performed by outsourced partners located primarily in China, India, and Vietnam.
[AAPL:S026] Operating cash flow was $110,543 million in fiscal 2023, compared to $122,151 million in fiscal 2022.
[AAPL:S027] Capital expenditures for property, plant, and equipment were $9,959 million in fiscal 2023, compared to $10,708 million in fiscal 2022.
[AAPL:S028] Free cash flow was $100,584 million in fiscal 2023 compared to $111,443 million in fiscal 2022.
[AAPL:S029] Total cash, cash equivalents, and marketable securities were $162,149 million as of September 30, 2023.
[AAPL:S030] Total term debt was $105,963 million, and commercial paper outstanding was $5,985 million as of September 30, 2023.
[AAPL:S031] During fiscal 2023, Apple repurchased $77,550 million of common stock and paid $15,025 million in cash dividends.
[AAPL:S032] Foreign exchange headwinds negatively affected total net sales by approximately 370 basis points in fiscal 2023.
[AAPL:S033] The Company's effective tax rate was 14.7% in fiscal 2023, compared to 16.2% in fiscal 2022.
[AAPL:S034] Total number of full-time equivalent employees was approximately 161,000 as of September 30, 2023.
[AAPL:S035] Manufacturing purchase obligations and other commitments totaled $41,403 million as of September 30, 2023.
"""

NIKE_TEXT = """[NKE:S001] NIKE, Inc. is the world's leading designer, marketer, and distributor of authentic athletic footwear, apparel, equipment, and accessories.
[NKE:S002] Fiscal year 2023 ended on May 31, 2023.
[NKE:S003] Total NIKE, Inc. revenues rose 10% to $51,217 million in fiscal 2023 compared to $46,710 million in fiscal 2022.
[NKE:S004] On a currency-neutral basis, revenues grew 16% in fiscal 2023, reflecting strong consumer demand across all geographies.
[NKE:S005] Gross margin contracted 250 basis points to 43.5% in fiscal 2023 from 46.0% in fiscal 2022.
[NKE:S006] The 250 basis point decrease in gross margin was primarily driven by higher markdowns to liquidate excess inventory, unfavorable net foreign currency exchange rates, and elevated freight and logistics costs, partially offset by strategic pricing actions.
[NKE:S007] Operating overhead expense increased 12% to $12,317 million, primarily due to wage-related expenses and strategic technology investments.
[NKE:S008] Demand creation expense was $4,060 million, an increase of 5% compared to $3,850 million in fiscal 2022, driven by advertising and sports marketing investments.
[NKE:S009] Net income decreased 16% to $5,070 million in fiscal 2023 compared to $6,046 million in fiscal 2022.
[NKE:S010] Diluted earnings per share decreased 14% to $3.23 in fiscal 2023 compared to $3.75 in fiscal 2022.
[NKE:S011] NIKE Direct revenues were $21,308 million, up 14% on a reported basis and 20% on a currency-neutral basis, led by NIKE-owned digital growth of 24%.
[NKE:S012] Wholesale revenues were $27,400 million, an increase of 7% on a reported basis and 14% on a currency-neutral basis.
[NKE:S013] Footwear revenues were $33,136 million, up 12% on a reported basis and 18% on a currency-neutral basis.
[NKE:S014] Apparel revenues were $13,945 million, up 3% on a reported basis and 8% on a currency-neutral basis.
[NKE:S015] Equipment revenues were $1,718 million, an increase of 6% (12% currency-neutral).
[NKE:S016] North America revenues increased 9% (8% currency-neutral) to $21,608 million.
[NKE:S017] Europe, Middle East & Africa (EMEA) revenues increased 8% (16% currency-neutral) to $13,418 million.
[NKE:S018] Greater China revenues declined 4% on a reported basis (increased 4% currency-neutral) to $7,248 million, heavily impacted by COVID-19 lockdowns in the first half of the year.
[NKE:S019] Asia Pacific & Latin America (APLA) revenues increased 8% (17% currency-neutral) to $6,431 million.
[NKE:S020] Converse brand revenues were $2,427 million, an increase of 3% on a reported basis and 8% currency-neutral.
[NKE:S021] During fiscal 2023, our largest customer, Foot Locker, Inc., accounted for approximately 6% of total NIKE Brand revenues.
[NKE:S022] No single customer accounted for 10% or more of consolidated net revenues in fiscal 2023, 2022, or 2021.
[NKE:S023] Inventories were $8,454 million as of May 31, 2023, flat compared to $8,420 million as of May 31, 2022, as supply chain lead times normalized.
[NKE:S024] Cash provided by operations was $5,841 million in fiscal 2023, compared to $5,188 million in fiscal 2022.
[NKE:S025] Capital expenditures were $906 million in fiscal 2023, compared to $757 million in fiscal 2022.
[NKE:S026] Free cash flow was $4,935 million in fiscal 2023, an increase of 11.4% from $4,431 million in fiscal 2022.
[NKE:S027] Cash, cash equivalents, and short-term investments totaled $10,675 million as of May 31, 2023.
[NKE:S028] Total debt was $12,141 million, including short-term borrowings and operating lease liabilities.
[NKE:S029] Share repurchases totaled $4,778 million and dividends paid totaled $2,023 million during fiscal 2023.
[NKE:S030] Independent contract manufacturers in Vietnam, Indonesia, and China manufactured approximately 50%, 27%, and 18% of NIKE brand footwear, respectively.
[NKE:S031] Independent contract manufacturers in Vietnam, China, and Cambodia manufactured approximately 28%, 16%, and 16% of NIKE brand apparel, respectively.
[NKE:S032] The effective tax rate was 18.2% in fiscal 2023, compared to 9.1% in fiscal 2022, primarily due to lower benefits from stock-based compensation and discrete items.
[NKE:S033] Worldwide employee headcount was approximately 83,700 as of May 31, 2023.
[NKE:S034] Total endorsements and promotional commitments amounted to $7,842 million as of May 31, 2023.
"""

def main():
    with open(os.path.join(FILINGS_DIR, "msft_10k_2023.txt"), "w") as f:
        f.write(MSFT_TEXT.strip() + "\n")
    with open(os.path.join(FILINGS_DIR, "aapl_10k_2023.txt"), "w") as f:
        f.write(AAPL_TEXT.strip() + "\n")
    with open(os.path.join(FILINGS_DIR, "nke_10k_2023.txt"), "w") as f:
        f.write(NIKE_TEXT.strip() + "\n")
    print("Filings written successfully.")

if __name__ == "__main__":
    main()
