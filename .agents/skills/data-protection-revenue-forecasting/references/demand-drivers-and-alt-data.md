# Exogenous Demand Drivers and External Data

*Everything OUTSIDE the vendor's own CRM that shifts the level or growth rate of demand, and the
observable public series that proxy for those drivers. Use this as the primary demand model when you
have no internal order flow, and as exogenous covariates when you do.*

**Module date: 2026-07-27.** All figures carry their source period. Vintages matter enormously here —
Gartner revised its 2026 IT spending forecast three times in six months.

**Conventions:**
- `[FLAG: RULE OF THUMB]` = practitioner heuristic, no empirical source.
- `[FLAG: WEAK SOURCE]` = traced only to a secondary aggregator or low-authority site; verify before use.
- `[FLAG: NO PUBLISHED EVIDENCE FOUND]` = searched, found nothing citable.

---

## A. Market sizing and growth baselines

### A.1 The data protection software market itself

The industry-standard vendor-revenue series is **IDC's Worldwide Semiannual Software Tracker, Data
Replication & Protection** segment. It covers data protection and recovery software, data-replication
services, and public cloud services
([Blocks & Files, 2024-04-22](https://www.blocksandfiles.com/data-protection/2024/04/22/idc-veeam-has-the-largest-share-of-the-data-protection-market-and-growing-fastest/1613112)).

- **Market size:** IDC's Semiannual Software Tracker, 2024H1 estimated the data replication and
  protection software market at **$12.3 billion in projected vendor sales for calendar 2024** — cited
  verbatim in [Cohesity's 2024-12-10 press release](https://www.cohesity.com/newsroom/press/cohesity-becomes-worlds-largest-data-protection-provider-after-completing-combination-with-veritas-enterprise-data-protection-business/).
  This is the most recent *attributable dollar* figure in the public domain; IDC does not publish
  current-year totals outside the paywalled tracker.
- **Growth, most recent read:** For **2H2025**, IDC reported market-average **sequential growth of
  8.8%** (half-over-half), with Veeam at **13.6% share** (up from 13.2% in 1H2025) and 11.5% sequential
  growth ([Veeam press release, 2026-04-28](https://www.veeam.com/company/press-release/veeam-ranked-the-no1-data-protection-software-in-market-share-worldwide-for-2h-2025.html)).
  **Caution:** "8.8% sequential" is half-over-half, not year-over-year, and it is disclosed through a
  vendor press release rather than IDC directly. Do not annualize it naively.
- **Fragmentation:** the leader holds ~13.6% share; the top five or six vendors hold roughly 55–60%
  combined ([StorageNewsletter, 2026-05-07](https://www.storagenewsletter.com/2026/05/07/veeam-ranked-the-1-data-protection-software-in-market-share-worldwide-for-2h-2025/)).
  Share shifts of 50–100 bps per half are normal and can swamp market growth for any single vendor.
- **Forecast character:** IDC's *Worldwide Data Protection Software Forecast, 2025–2029* (Aug 2025, doc
  [US53577825](https://my.idc.com/getdoc.jsp?containerId=US53577825&pageType=PRINTFRIENDLY)) states the
  market "is largely immune to budget reduction and continues to grow steadily, even when economic
  conditions force organizations to make cuts elsewhere." The prior-year edition similarly described it
  as "highly resilient," with fastest growth in public cloud services rather than on-prem licences.

Vendor-claimed TAMs are much larger and should be treated as marketing: Cohesity claims a "$40+ billion
TAM" that *includes* the IDC $12.3B market plus adjacencies (same press release).

### A.2 IT and software spending

Gartner's IT spending forecast is the standard top-down anchor. Latest vintage (**2026-07-27**):
worldwide IT spending of **$6.37 trillion in 2026, +14.2%**, with **software at $1,468B, +15.5%** and
data center systems +62.5%
([Gartner newsroom](https://www.gartner.com/en/newsroom/press-releases/2026-07-27-gartner-forecasts-worldwide-it-spending-to-grow-14-point-2-percent-in-2026-totaling-6-point-37-trillion)).

The revision history is the more useful signal: software growth for 2026 was forecast at 15.2% (Oct
2025) → 14.7% ([Feb 2026](https://www.gartner.com/en/newsroom/press-releases/2026-02-03-gartner-forecasts-worldwide-it-spending-to-grow-10-point-8-percent-in-2026-totaling-6-point-15-trillion-dollars))
→ 15.1% ([Apr 2026](https://www.businesswire.com/news/home/20260422301495/en/Gartner-Forecasts-Worldwide-IT-Spending-to-Grow-13.5-in-2026-Totaling-%246.31-Trillion))
→ 15.5% (July 2026). **The top-down anchor itself has ±50–80 bps of revision noise per quarter, which
sets a floor on how precise your driver-based adjustments can meaningfully be.**

Critically, most of the 2026 IT acceleration is AI infrastructure and GenAI model spending, *not*
infrastructure software. Do not pass through headline IT growth to data protection.

### A.3 Storage systems (related but distinct)

**IDC Worldwide Quarterly Enterprise Storage Systems Tracker, 1Q26:** external OEM ESS vendor revenue
of **$9.2B, +22.7% YoY**, versus full-year 2025 of **$33.0B, +3.9%**. All-flash arrays crossed 50% of
revenue for the first time at $4.9B, +32.7%
([IDC via BizTechReports, 2026-07-13](https://www.biztechreports.com/news-archive/2026/7/6/worldwide-external-enterprise-storage-systems-market-accelerates-to-227-growth-in-the-first-quarter-of-2026-driven-by-ai-infrastructure-demand-and-deferred-refresh-spending-idc-july-09-2026);
[Blocks & Files](https://www.blocksandfiles.com/flash/2026/06/16/idc-ranks-dell-netapp-everpure-huawei-and-hpe-in-external-storage-systems-market/5256070)).
IDC's public tracker page forecasts **7.3% CAGR through 2030**
([idc.com](https://www.idc.com/promo/enterprise-storage-systems/)).

IDC explicitly attributes part of the 1Q26 acceleration to **component price inflation (NAND, DRAM)
raising system ASPs** — revenue growth exceeding unit growth. Storage systems is a *leading and
correlated* series for appliance-attached data protection (Dell PowerProtect, purpose-built backup
appliances) but a poor proxy for software-only vendors.

### A.4 Data growth, and why it is not a revenue driver

IDC's **Global DataSphere** measures data *created, captured, replicated and consumed* per year:
**132,425 EB in 2023 → 393,852 EB in 2028, a 24.4% CAGR**
([IDC US52554824, Sep 2024](https://techcontentwave.com/files/1763389937_64b594fd4f7f5607256a.pdf)).

The same document contains the number that kills naive TAM math: **data *created* grows at a 25.1%
2023–2028 CAGR, while data *stored* (Global StorageSphere) grows at ~16.x%.** IDC states plainly: "IDC's
Global DataSphere is a measure of how much new data is created each year. It is not a measure of how
much data is stored."

Four wedges separate data growth from revenue growth:

1. **Creation → storage:** ~9 points of CAGR lost to ephemeral/cached data.
2. **Storage → protected capacity:** deduplication, compression, incremental-forever and change-block
   tracking mean logical protected data grows far faster than physical backup footprint.
   `[FLAG: RULE OF THUMB]` vendor-cited dedup+compression ratios run 3:1 to 20:1 by workload; there is
   **no** independent published measurement of the aggregate industry ratio.
   `[FLAG: NO PUBLISHED EVIDENCE FOUND]`
3. **Pricing model shift:** per-TB pricing is being displaced by per-workload/per-VM/per-user
   subscription, which decouples revenue from capacity entirely.
4. **Price-per-TB deflation:** historically the dominant offset. `[FLAG: NO PUBLISHED EVIDENCE FOUND]` —
   no published time series of data-protection software effective price per protected TB exists.

**Use data growth as a qualitative floor argument, never as a multiplier.**

---

## B. Named demand catalysts

### B.1 Ransomware incidence and severity

| Series | Latest | Prior | Source |
|---|---|---|---|
| IC3 ransomware complaints | 3,611 (2025) | 3,156 (2024); 2,825 (2023) | [FBI IC3 2025 Annual Report](https://www.phishingbox.com/downloads/FBI-2025-Internet-Crime-Report-IC3Report.pdf) |
| IC3 total cybercrime losses | $20.877B (2025), +26% | $16.6B (2024) | [McDonald Hopkins summary](https://www.mcdonaldhopkins.com/insights/news/the-sobering-truth-of-the-fbis-2025-internet-crime-complaint-center-report) |
| Chainalysis on-chain ransom payments | ~$820M (2025), −8% | $892M (2024 revised) | [Chainalysis 2026 Crypto Crime Report](https://www.chainalysis.com/blog/crypto-ransomware-2026/) |
| Claimed attacks | +50% YoY (2025), record | — | Chainalysis, same |
| Median ransom payment | $59,556 (2025), +368% | $12,738 (2024) | Chainalysis, same |
| Victim payment rate | ~28–29%, all-time low | 63% (2024) | Chainalysis, same |
| Ransomware share of breaches | 48% (DBIR 2026) | 44% (DBIR 2025) | [Verizon 2026 DBIR](https://www.verizon.com/business/resources/T235/reports/2026-dbir-data-breach-investigations-report.pdf) |
| Victims not paying | 69% | — | Verizon 2026 DBIR |
| Backups used to restore | 54% (lowest in 6 yrs) | 3rd consecutive decline | [Sophos State of Ransomware 2025](https://assets.sophos.com/X24WTUEQ/at/9brgj5n44hqvgsp5f5bqcps/sophos-state-of-ransomware-2025.pdf) |
| Mean recovery cost ex-ransom | $1.53M | $2.73M (2024), −44% | Sophos, same |
| Fully recovered within a week | 53% | 35% (2024) | Sophos, same |

**Direction is genuinely ambiguous, and this is the most important honest observation in this module.**
Incidence is clearly up (attacks +50%, ransomware in 48% of breaches). But *severity of outcome is
falling*: payments down, payment rates at record lows, recovery costs down 44%, recovery speed sharply
improved. A forecaster who reads only the incidence series will over-forecast.

Note the tension: Sophos finds backup-based restoration at a six-year low (54%) while recovery times
improved sharply. Both cannot be flattering to the "backup software is winning" narrative.

**Mechanism and lag:** incident → board/audit committee attention → unbudgeted or next-cycle budget
line → purchase of immutability, air-gapped copy, isolated recovery environment, or cyber-vault.
`[FLAG: RULE OF THUMB]` practitioner lag estimates are one to three quarters from incident to closed
deal for the victim, and the more important effect is *sector-level*: a marquee incident in a vertical
pulls forward peer spending. No published study quantifies either the lag or the peer-contagion effect.
`[FLAG: NO PUBLISHED EVIDENCE FOUND]`

### B.2 Cyber insurance underwriting

**Premium trend is a headwind, not a tailwind.** Marsh's Global Insurance Market Index for **Q2 2026**
(published 2026-07-23) reports **cyber insurance rates down 4% globally — the twelfth consecutive
quarter of declines** — following −5% in Q1 2026; US cyber rates have been declining since Q2 2023
([Marsh](https://www.corporate.marsh.com/news-events/2026/july/global-commercial-insurance-falls-6-percent-q2-2026.html);
[Insurance Journal](https://www.insurancejournal.com/news/national/2026/07/23/878716.htm)).

**Underwriting rigor is the tailwind.** Carriers have shifted from questionnaires to technical
verification, with immutable/offline backups and *tested* restores as standard conditions; failure to
maintain them can convert into claim denial. A widely circulated figure — that **82% of policies now
include offline/immutable backup requirements, up from 45% in 2022, attributed to Munich Re** — appears
only in secondary aggregations ([medhacloud](https://medhacloud.com/blog/cyber-insurance-statistics-2026)).
`[FLAG: WEAK SOURCE]` Obtain the Munich Re Cyber Insurance report directly before using it.

**Net read:** insurance is a *specification* driver (it dictates *what* gets bought — immutability, air
gap, tested recovery) far more than a *volume* driver. Softening premiums arguably reduce urgency.

### B.3 Regulation

| Regime | In scope | What it forces | Dates |
|---|---|---|---|
| **EU DORA** (Reg. 2022/2554) | 20–21 categories of EU financial entities plus designated critical ICT third parties | Art. 12: documented backup policy, restoration/recovery procedures, **periodic testing**; Art. 12(3) restoration onto systems **physically and logically segregated** from source; Art. 12(7) post-incident integrity checks; redundant ICT capacity | In force 2023-01-16; **applies 2025-01-17** ([ESMA](https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/digital-operational-resilience-act-dora); [EIOPA](https://www.eiopa.europa.eu/digital-operational-resilience-act-dora_en); [BaFin implementation notes](https://www.bafin.de/SharedDocs/Downloads/EN/Anlage/dl_2024_07_08_Aufsichtsmitteilung_Umsetzungshinweise_DORA_en.pdf?__blob=publicationFile&v=3)) |
| **NIS2** (Dir. 2022/2555) | 18 critical sectors, essential + important entities | Art. 21 measures incl. business continuity, **backup management**, disaster recovery, crisis management; management-body accountability | Transposition due 2024-10-17. Only 4 states met it; Commission opened infringements against 23 states (2024-11-28) and **referred Ireland, Spain, France and the Netherlands to the CJEU** ([European Commission](https://digital-strategy.ec.europa.eu/en/policies/nis-transposition)). ~two-thirds transposed by mid-2026 ([ECSO tracker](https://ecs-org.eu/policy/nis2-directive-transposition-tracker/)). **The forecast-relevant date is the national go-live, not 2024.** |
| **SEC cyber disclosure** | US registrants | Item 1.05 8-K within four business days of a materiality determination; Reg S-K Item 106 annual disclosure. Drives *governance and readiness* spend, not backup directly | Adopted 2023-07-26. Still in effect mid-2026 but under deregulatory pressure: five banking trade bodies petitioned for rescission (May 2025) and filed a joint comment letter 2026-04-10 urging rescission of both items ([SIFMA](https://www.sifma.org/advocacy/letters/reforming-regulation-s-ks-cybersecurity-disclosures-joint-trades); [Debevoise](https://www.debevoisedatablog.com/2025/05/27/financial-services-industry-petitions-the-sec-for-a-rulemaking-to-amend-the-cybersecurity-risk-management-strategy-governance-and-incident-disclosure-rule/)). **Treat as a decaying driver.** |
| **HIPAA Security Rule update** | US covered entities + business associates | Proposed: all specifications mandatory, **72-hour ePHI restoration**, additional backup/recovery controls and testing, annual pen tests | NPRM 2025-01-06, comments closed 2025-03-07. **Not final.** OMB Unified Agenda (RIN 0945-AA22) now lists final action **July 2027**, moved from May 2026 ([McDermott](https://www.mcdermottlaw.com/insights/final-action-on-hipaa-security-rule-modifications-now-projected-for-july-2027/)). With a ~180–240 day compliance window, realistic spend lands **2028**. **Any 2026 forecast crediting HIPAA-driven demand is wrong.** |
| **UK FCA/PRA operational resilience** | UK dual-regulated firms | Impact tolerances for important business services, scenario testing | `[FLAG: NO PUBLISHED EVIDENCE FOUND]` — current milestone dates not verified in this pass. Check FCA PS21/3 and successors before use. |

**Forecasting note:** regulation is the most over-credited driver in this sector because compliance
dates are visible and quotable. But DORA's date has passed (spend is in the base), NIS2 is fragmenting
into 27 national timelines, HIPAA has slipped two years, and SEC rules may be rescinded. On net, the
2026–2027 regulatory impulse for data protection is **weaker** than 2024–2025, not stronger.

### B.4 Broadcom/VMware and hypervisor migration

- **Gartner's 2026 Sentiment on Broadcom Ownership of VMware Survey** (fielded 2026-01-20 to 01-28,
  n=182 IT leaders/CIOs): 76% negative outlook (up from 64% in 2025 and 33% in 2024); **67% actively or
  passively pursuing alternatives**; 35% have completed or intend to migrate their entire portfolio.
  Cited via [a vendor blog quoting Gartner G00847021](https://www.arcfra.com/blog/vmware_modernization_2026_roadmap_q001).
  `[FLAG: WEAK SOURCE]` — obtain the Gartner document directly.
- **CloudBolt survey, n=302 North American IT decision-makers (2026):** **86% actively reducing VMware
  footprint**, and **only 4% fully migrated off VMware**
  ([Channel Dive](https://www.channeldive.com/news/broadcom-vmware-migrations-costs-cloudbolt-report/812735/)).
- Named migrations at scale: Computershare 24,000 VMs to Nutanix; Beeks Group >20,000 VMs to OpenNebula;
  Boyd Gaming 5,100 VMs to Nutanix over 18 months; Stanford ~1,500 VMs to Proxmox
  ([practitioner compilation](https://www.yeandel.co.uk/22-q3-2026-updates/vmware-exodus-where-they-went.html)).

**Mechanism:** backup products are licensed and architected per-hypervisor. A hypervisor change forces
a data-protection re-evaluation, because incumbent agents, changed-block-tracking integrations and
image-level backup support must be re-certified. This creates a **forced-decision event** — the highest-
conversion event type in this market. Vendors with early Proxmox/AHV/Hyper-V support capture
displacement; vendors whose differentiation was VMware-specific face churn.

**Direction:** positive for challengers, mixed for incumbents, and a **multi-year, slow-diffusing
driver** — 4% completed after two years, with 18–48 month project timelines. Do not model it as a step
function.

### B.5 Microsoft 365 / SaaS backup

Microsoft 365 Backup reached GA **2024-07-31** at a list price of **$0.15/GB/month of protected
content**, billed on live data plus recycle bins, online archives and retained versions
([Microsoft Learn pricing](https://learn.microsoft.com/en-us/microsoft-365/backup/backup-pricing?view=o365-worldwide);
[GA announcement](https://techcommunity.microsoft.com/blog/microsoft_365blog/microsoft-announces-general-availability-of-microsoft-365-backup-and-microsoft-3/4205300)).

The strategically important design choice: Microsoft also shipped **Microsoft 365 Backup Storage APIs**
and positioned ISVs as builders on top of it, with launch partners AvePoint, Cohesity, Commvault,
Rubrik, Veeam and Veritas. When a customer uses an ISV solution built on the platform, **Microsoft bills
the ISV, not the customer** ([pricing doc](https://learn.microsoft.com/en-us/microsoft-365/backup/backup-pricing?view=o365-worldwide)).

**Two-sided read:** it is a floor on price for basic M365 backup (a commoditization risk to per-seat
pricing), *and* a COGS line for ISVs who build on it, *and* a TAM expander because it legitimizes the
shared-responsibility argument. `[FLAG: NO PUBLISHED EVIDENCE FOUND]` — no published study measures the
net effect on third-party M365 backup vendor ARR since GA. Model it as an ASP headwind of unknown
magnitude rather than a unit headwind.

### B.6 Kubernetes and AI/ML data protection

Sizing evidence is **poor and should be treated as unusable for forecasting**. Three market-research
vendors give: $0.8B (2025) → $1.02B (2026), 27.7% CAGR
([TBRC](https://www.thebusinessresearchcompany.com/report/kubernetes-backup-software-global-market-report));
$1.2B (2025) → $9.8B (2034) ([MarketIntelo](https://marketintelo.com/report/kubernetes-backup-software-market));
and $582.6M (2025) → $2.48B (2035), 15.6% CAGR ([Market.us](https://market.us/report/kubernetes-backup-software-market/)).
**A 2× spread in the base year and a 12-point spread in CAGR means none of these are measurements.**
`[FLAG: WEAK SOURCE]`

For AI/ML artifacts (vector databases, model checkpoints, feature stores, GPU-adjacent scratch storage):
`[FLAG: NO PUBLISHED EVIDENCE FOUND]` — no credible independent sizing. Vendor positioning has moved
aggressively here (Veeam's $1.725B Securiti AI acquisition closed 2025-12-11), which is evidence of
*expected* demand, not realized demand.

### B.7 Cloud migration vs. repatriation

The famous number is soft and widely misused. **Barclays CIO Survey Q4 2024: 83% of CIOs planned to move
at least some workloads from public cloud back to private/on-prem — the highest the survey had recorded,
up from 43% in 2020.** Some write-ups report 86%; treat the precise figure as soft.

The counterweight: **IDC finds ~80% of enterprises expect to repatriate some compute or storage within
12 months, but only ~8–9% are moving entire workloads off cloud**
([analysis of the statistical artifact](https://www.channelnomics.com/insights/breaking-down-the-83-public-cloud-repatriation-number)).
The Barclays question counts *companies*, not *workloads*.

**Forecast implication:** both directions raise data-protection spend transiently, because either move
forces a protection re-architecture, and hybrid steady-state means paying for protection in *two*
places. But the net capacity effect is close to a wash. `[FLAG: RULE OF THUMB]` Model repatriation as a
driver of *deal count and hybrid SKU attach*, not of aggregate capacity.

### B.8 Cloud marketplaces

**Tackle's State of Cloud GTM report (Nov 2025)** surveyed B2B software companies: marketplace revenue
share expected to rise from **20% of total software revenue over the trailing 12 months to 32% in the
coming year**. Drivers cited: access to committed cloud provider spend (75%), deal acceleration (47%),
partner incentives (43%) ([Tackle PDF](https://tackle.io/wp-content/uploads/2025/11/SOCGTM-Report-2025.pdf)).

**Omdia** projects **60% of all marketplace purchases delivered through channel partners by 2030**,
enabled by AWS Channel Partner Private Offers, Microsoft Multiparty Private Offers and Google
Marketplace Channel Private Offers
([Omdia via Red Hat, Feb 2026](https://www.redhat.com/rhdc/managed-files/cl-omdia-hyperscaler-marketplaces-analyst-material-3529349-202602-en.pdf)).

**Mechanism that matters for a revenue model:** private offers let the buyer draw down an existing AWS
EDP / Azure MACC / GCP commitment. This changes *whose budget* is spent — moving the purchase out of a
scrutinized software line into pre-committed cloud spend — which compresses procurement cycles and
raises deal size. Marketplace-listing status and private-offer capability are therefore **observable,
forecast-relevant vendor attributes**.

### B.9 Hardware and media cost curves

- Western Digital's CEO stated the company is **"pretty much sold out for calendar 2026,"** with some
  enterprise agreements extending to 2028; HDD prices up ~46% since September 2025
  ([Yahoo Finance summary of the call](https://finance.yahoo.com/news/hard-drives-sold-2026-ai-173205634.html)).
- IDC attributes part of 1Q26 storage revenue acceleration explicitly to **NAND and DRAM price inflation
  raising system ASPs**, and expects pressure to persist through 2026
  ([Blocks & Files on IDC 1Q26](https://www.blocksandfiles.com/flash/2026/06/16/idc-ranks-dell-netapp-everpure-huawei-and-hpe-in-external-storage-systems-market/5256070)).

Specific $/TB levels circulating on low-authority sites are `[FLAG: WEAK SOURCE]` — directionally
consistent with WD/IDC but do not quote the levels.

**Effects to model:**
- **Software-only vendors:** mildly *positive*. Rising target-storage cost strengthens the ROI case for
  dedup/compression efficiency and tiering.
- **Appliance-attached vendors** (Dell PowerProtect, PBBAs, Cohesity/Veritas appliance mix):
  *revenue-positive, margin-negative* — ASPs rise with BOM cost, gross margin compresses, unit demand
  can be deferred.
- **Cloud-target/BaaS vendors:** COGS headwind if their storage tier reprices.
- Watch Samsung, SK Hynix, Micron, Seagate and WD earnings as the leading indicator for relief; NAND fab
  capacity takes 2–3 years, so 2027 is the earliest meaningful normalization.

### B.10 Macro and the "non-discretionary" thesis

The thesis has real support, but it is **relative, not absolute** resilience.

**2008–09 evidence.** Commvault — then almost a pure-play backup vendor, with backup/recovery at 72% of
software revenue ([FY2009 10-K](https://www.sec.gov/Archives/edgar/data/1169561/000089322009001231/w74075e10vk.htm))
— grew full-year FY2009 revenue **+18%**, but its **Q4 FY2009 (Jan–Mar 2009) revenue fell 1% YoY and
software revenue fell 12% YoY**
([Commvault FY2009 results](https://ir.commvault.com/news-releases/news-release-details/commvault-announces-fourth-quarter-and-fiscal-year-end-2009)).

**The recovery shape is the real lesson.** IDC's Q1 2010 storage software tracker: total storage software
+7.2% YoY, with **data protection and recovery +10.6%** — attributed by IDC to "the release of storage
spending, following budget freezes in 2009 and the increase of backlog projects that are starting to be
switched on again"
([Commvault citing IDC](https://ir.commvault.com/news-releases/news-release-details/commvault-continues-gain-market-share-while-outpacing-storage);
[The Register, 2010-06-09](https://www.theregister.com/2010/06/09/emc_storage_sw_q1_2010/)).

**Conclusion: data protection is deferrable, not cancellable.** Downturns produce a one-to-three-quarter
air pocket in new licence/expansion bookings with renewals largely intact, followed by catch-up. IDC's
"largely immune to budget reduction" characterization is directionally right but overstated relative to
the 2009 microdata.

### B.11 Competitive and structural

- **Cohesity–Veritas** closed **2024-12-10**: pro forma FY-ending-July-2024 revenue >$1.7B, **ARR
  $1.5B**, 28% adjusted cash EBITDA margin, >12,000 customers, valued at >$7B
  ([Cohesity](https://www.cohesity.com/newsroom/press/cohesity-becomes-worlds-largest-data-protection-provider-after-completing-combination-with-veritas-enterprise-data-protection-business/)).
  Cohesity is reported to be eyeing a 2026 IPO. `[FLAG: WEAK SOURCE]`
- **Veeam:** $1.7B ARR as of September 2024, +18% YoY, at a $15B valuation in an Insight Partners
  secondary ([Reuters, 2024-12-04](https://www.reuters.com/markets/deals/insight-partners-sells-2-bln-stake-data-firm-veeam-15-bln-valuation-2024-12-04/)).
  Completed **Securiti AI for $1.725B on 2025-12-11**.
- **Public comparables (the autocorrelation prior):** Rubrik FY2026 subscription ARR **$1.462B, +34%**,
  guiding FY2027 to **$1.829–1.839B, +25–26%**. Commvault FY2026 total ARR **$1.122B, +21%**; subscription
  ARR **$989M, +27%**; SaaS ARR **$400M, +42%**; total revenue $1,184M, +19%.

**Structural mechanisms to carry into a model:** (a) merger-integration years create displacement
windows — renewal events at the merged entity are contestable; (b) an IPO forces a private competitor
toward disclosed-metric discipline, which historically means *more* sales capacity investment and *more*
price aggression in the pre-IPO and first-year-public windows `[FLAG: RULE OF THUMB]`; (c) Dell and IBM
bundling means their data-protection revenue is partly a function of their *hardware* attach motion, so
their share moves with storage/server cycles rather than data-protection demand.

---

## C. Observable proxy series for an outside-in forecaster

| Signal | Source / URL | Frequency | Lead–lag vs. vendor revenue | Access | Known pitfalls |
|---|---|---|---|---|---|
| **Quota-carrying rep job postings** | Company career sites; LinkUp; Thinknum; Revelio | Daily | **Leads ~2–4 quarters.** Best-evidenced signal here: postings positively predict one-year-ahead growth in headcount, SG&A, **sales** and earnings ([Gutierrez, Lourie, Nekrasov & Shevlin, *Management Science*](https://doi.org/10.1287/mnsc.2019.3450)) | Free (scrape); paid | Must separate growth from replacement hiring — the paper's central caveat. Reposts inflate counts |
| **LinkedIn headcount** | LinkedIn pages / Revelio Labs | Weekly | Coincident to slightly lagging | Free / paid | Self-reported; acquisitions cause discontinuities; regional profile-density bias |
| **Glassdoor reviews/ratings** | glassdoor.com | Continuous | Lagging, and about morale not demand | Free | Selection bias; layoff-driven review bombing. **Folklore for revenue purposes** |
| **Web traffic (Similarweb)** | [similarweb.com](https://www.similarweb.com/) | Daily, ~3–7 day lag | **Leads by weeks within the quarter.** Documented: digital-traffic changes predict revenue surprises vs consensus ([Berkeley Haas working paper](http://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/DigitalTraffic_Full.pdf)) | Paid | Evidence strongest for consumer/e-commerce and PLG. **For enterprise field-sales vendors the link is much weaker** |
| **Trial/download/PLG signals** | Vendor free-tier pages, Docker Hub pulls, Helm downloads | Weekly | Leads 1–3 quarters where a real PLG motion exists (Veeam Community Edition, Kasten) | Free/partial | Only meaningful with genuine self-serve. Bots and CI dominate container pull counts |
| **Google Trends** | [trends.google.com](https://trends.google.com) | Weekly | Weak lead; useful for *category* shifts ("Proxmox backup," "VMware alternative") | Free API | Relative index, re-normalizes; brand searches conflate support traffic with intent. **Mostly folklore at the vendor level** |
| **G2 / Gartner Peer Insights review velocity** | [g2.com](https://www.g2.com/), [gartner.com/reviews](https://www.gartner.com/reviews/market) | Monthly | Coincident-to-lagging; reflects vendor review *campaigns* | Free | Heavily gamed via gift-card incentives. Use as *relative* momentum across vendors in the same window |
| **Partner-program directory counts** | Veeam ProPartner, Commvault, Rubrik locators | Quarterly scrape | Leads 2–4 quarters for channel-led vendors | Free | Stale listings; tier inflation; dormant partners never delisted |
| **Cloud marketplace listings + reviews** | AWS / Azure / GCP Marketplace | Continuous | Listing breadth leads; review counts coincident | Free | Reviews sparse. Private-offer volume — the number that matters — is **not public** |
| **GitHub / community activity** | GitHub API, vendor forums, r/sysadmin, r/Proxmox | Daily | Leads for open-core and Kubernetes-native products | Free API | Irrelevant for closed-source enterprise suites |
| **Conference/event announcements** | VeeamON, Commvault SHIFT, Rubrik Forward, KubeCon | Annual | Coincident with product cycle, not demand | Free | Announcements ≠ GA ≠ revenue |
| **SEC filings of public customers** | EDGAR full-text search; Item 1.05 8-K trackers | Continuous | **Item 1.05 filings lead vendor bookings by 1–3 quarters** for the filer and vertical peers `[FLAG: RULE OF THUMB]` | Free | Item 1.05 may be rescinded (B.3) — the series could stop. Filers increasingly use Item 8.01 instead |
| **Channel-partner / distributor earnings** | TD Synnex, Arrow, Ingram, CDW, Insight, SHI | Quarterly | **Coincident to ~1 quarter lead** | Free | Aggregation is the killer. TD Synnex FQ2'26 revenue $19.6B, +31% ([TD Synnex](https://news.tdsynnex.com/news/td-synnex-reports-record-fiscal-2026-second-quarter-results/)) is dominated by AI infrastructure, not backup. Call Q&A commentary is worth more than the segment number |
| **Hyperscaler earnings commentary** | AWS/Azure/GCP calls | Quarterly | Coincident | Free | Cloud growth is a *substitution* signal as much as a demand signal |
| **Memory/HDD supplier earnings** | Micron, Samsung, SK Hynix, Seagate, WDC | Quarterly | **Leads target-storage cost by 1–2 quarters** | Free | Cycle turns are mis-timed by the suppliers themselves |

**Honest ranking of predictive value.** Documented in peer-reviewed literature: job postings (strong)
and web traffic (strong for consumer/PLG, unvalidated for enterprise field sales). Mechanically sound
but unvalidated: partner directory counts, marketplace listing breadth, Item 1.05 filings, distributor
earnings, memory-supplier earnings. **Folklore:** Glassdoor, Google Trends at the vendor level, review
velocity, conference announcements, LinkedIn headcount as a revenue predictor.

---

## D. Translating drivers into forecast adjustments

### D.1 The recommended mechanic

Do **not** do this: "ransomware incidence +20%, so raise growth 20% × assumed pass-through."

Do this instead:

1. **Start from the autocorrelation prior.** Fit `g_t = α + β·g_{t−1} + ε_t` on the vendor's own 8–12
   quarters of ARR growth, and pool across public comparables for shrinkage. For mature-to-growth
   infrastructure software, β is high — Rubrik went 34% actual → 25–26% guided; Commvault subscription
   ARR 27% → guided 18–19% on the recast base. The empirical regularity is **smooth deceleration**, not
   driver-driven jumps.
2. **Express each driver as a bounded prior on the deviation** `δ_j` from that baseline, in growth-rate
   points, with an explicit sign and an explicit cap. E.g.
   `VMware displacement: δ ~ Normal(+1.5pp, 1.0pp), truncated to [0, +4pp]`. The truncation is the
   discipline: it forces you to state the largest effect you would defend.
3. **Sum in log-growth space with an explicit overlap matrix.** Ransomware, cyber insurance and
   regulation all route through the *same* budget line and the *same* purchase (immutability + tested
   recovery). Adding them independently triple-counts. Group drivers into **mutually exclusive mechanism
   buckets** — (i) cyber-resilience budget, (ii) platform-change forced decisions, (iii) workload
   expansion (SaaS/K8s/AI), (iv) pricing/ASP, (v) macro/budget timing — and allow at most one driver to
   set the prior per bucket, with the others only tightening or widening its variance.
4. **Cap the total.** `[FLAG: RULE OF THUMB]` Constrain the sum of all driver deviations to roughly ±1/3
   of baseline growth. If your drivers move a 20% grower to 32%, you have written a story, not a forecast.
5. **Reconcile top-down.** Your implied market growth must be within a defensible band of the IDC tracker
   (~8.8% half-over-half most recently) plus a stated, justified share-gain assumption.

### D.2 Elasticity evidence

**No published estimate exists of the elasticity of data-protection spend to ransomware incidence, to
regulatory deadlines, or to IT budget growth.** `[FLAG: NO PUBLISHED EVIDENCE FOUND]` Not in IDC's public
abstracts, not in academic literature, not in sell-side research surfaced by search. Anyone quoting such
an elasticity is almost certainly quoting a vendor.

The closest usable anchors, all indirect:

- **Budget elasticity:** Commvault's FY2009 — full-year +18% while the trough quarter's software revenue
  fell 12% YoY — implies a *high short-run* sensitivity of new-licence bookings to budget shock and a
  *low* sensitivity of the recurring base.
- **Recovery elasticity:** the 2010 catch-up (data protection & recovery +10.6% vs storage software
  +7.2%) implies deferred demand is largely recovered, not lost.
- **Severity elasticity is possibly negative right now.** Recovery costs fell 44% and 53% of victims
  recover within a week. If organizations perceive ransomware as *survivable*, the urgency premium falls
  even as incidence rises.

**How to bound it in the absence of evidence.** Use a *revealed-preference ceiling*: the entire market
grew ~8.8% half-over-half in the most favorable recent ransomware environment on record (attacks +50%,
DBIR at 48% of breaches). Therefore **no single driver can plausibly be worth more than a few points of
market growth**, because all drivers together did not produce more than that. Set every individual
driver's prior mean at ≤2pp and its truncation at ≤4pp unless you have vendor-specific order-flow
evidence.

### D.3 Guardrails against narrative-driven forecasting

1. **Every year has a compelling catalyst story.** 2021: ransomware and Colonial Pipeline. 2022–23: cyber
   insurance hardening. 2024: DORA countdown and Broadcom/VMware. 2025: DORA go-live and M365 Backup.
   2026: AI data protection and hypervisor migration. Market growth stayed in a narrow high-single-digit
   band throughout. **A catalyst that does not move the aggregate series is not a catalyst; it is a
   share-shift mechanism.** Route catalysts to *share* assumptions, not *market* assumptions, unless you
   can show the aggregate moved.
2. **Base rate first, story second.** Write down the autocorrelation-implied growth *before* reading any
   driver research. Timestamp it. If drivers routinely move your number by more than a few points, your
   process is narrative-driven.
3. **Check driver-story symmetry.** For 2026, honest accounting gives at least four *negative* exogenous
   items: cyber insurance rates down 4% for a twelfth straight quarter, ransom severity and recovery cost
   falling, HIPAA slipping to a projected July 2027 final action, and SEC Item 1.05 under rescission
   pressure. If your driver list is all positive, you have selected on the narrative.
4. **Watch the vintage.** Gartner revised 2026 software growth 15.2 → 14.7 → 15.1 → 15.5% within nine
   months. Re-date every exogenous input each quarter and refuse to use any driver figure older than 18
   months without re-verification.
5. **Distinguish deferrable from cancellable.** The 2009 evidence says the correct recession adjustment
   is a *timing* shift in new bookings plus a small renewal-rate haircut — not a level cut to the
   recurring base.
6. **Prefer forced-decision events over sentiment.** Hypervisor migrations, M&A-driven renewal contests
   and Item 1.05 filings are *events with dates*. Survey sentiment (76% negative on Broadcom, 83%
   planning repatriation) has repeatedly failed to convert at anything near the stated rate — only 4% of
   VMware customers had fully migrated after two years, and only 8–9% of repatriation intenders are
   moving whole workloads. **Discount all stated-intent survey data by the observed conversion rate
   whenever one is available.**
