"""Starter sustainability catalogue.

Loaded on demand from the admin console. Courses are created as unpublished
drafts so EinTrust's consultants can review, extend and publish them.
"""
from . import db

INSTRUCTOR = "EinTrust Sustainability Team"

STARTER_COURSES = [
    {
        "course": dict(
            title="Fundamentals of ESG",
            subtitle="Understand Environmental, Social and Governance performance and why it matters",
            description=(
                "A plain-language introduction to ESG for professionals who are new to sustainability. "
                "Learn what ESG covers, how materiality works, and how the main reporting frameworks fit together."
            ),
            learning_outcomes=(
                "Explain the E, S and G pillars with practical examples\n"
                "Distinguish ESG from traditional CSR\n"
                "Describe financial, impact and double materiality\n"
                "Navigate the major frameworks: GRI, ISSB, ESRS, BRSR and CDP"
            ),
            category="ESG Fundamentals", level="Beginner", duration_hours=2, price=0,
        ),
        "modules": [
            ("What is ESG?", "Article", """
**ESG** describes how an organisation manages risks and opportunities across three areas:

| Pillar | Typical topics |
|---|---|
| **Environmental** | Greenhouse gas emissions, energy, water, waste, biodiversity, pollution |
| **Social** | Health & safety, labour practices, human rights, diversity & inclusion, community impact |
| **Governance** | Board oversight, ethics & anti-corruption, risk management, transparency, executive pay |

**ESG vs CSR.** Corporate Social Responsibility is often about philanthropy and programmes *alongside* the
business. ESG is about how sustainability issues affect, and are affected by, the *core* business, and it is
measured with data that investors, lenders, customers and regulators can compare.

**Why it matters now:** investor and lender expectations, mandatory disclosure regulations, customer and
supply-chain requirements, and the physical and transition risks of climate change.
"""),
            ("Materiality: deciding what matters", "Article", """
Not every topic is equally important to every company. A **materiality assessment** identifies the issues that
matter most.

- **Financial materiality** – sustainability matters that affect the company's cash flows, cost of capital or
  enterprise value (the investor lens used by the ISSB standards).
- **Impact materiality** – the company's actual and potential impacts on people and the environment
  (the lens used by GRI).
- **Double materiality** – a topic is material if it is material from *either* perspective. This is the basis
  of the EU's European Sustainability Reporting Standards (ESRS).

A typical process: understand the context → identify topics → engage stakeholders → assess and prioritise →
validate with leadership → review regularly.
"""),
            ("The reporting framework landscape", "Article", """
- **GRI Standards** – the most widely used standards for reporting an organisation's impacts.
- **ISSB (IFRS S1 & S2)** – global baseline of investor-focused sustainability and climate disclosures; builds
  on the TCFD recommendations.
- **ESRS / CSRD** – mandatory, double-materiality reporting for companies in scope of the EU's CSRD.
- **BRSR** – SEBI's Business Responsibility and Sustainability Report for India's largest listed companies.
- **CDP** – a global disclosure platform through which companies respond to investor and customer requests on
  climate, water and forests.

Frameworks increasingly reference each other, so one well-built data set can serve several of them.
"""),
            ("Knowledge check: ESG fundamentals", "Quiz", ""),
        ],
        "quiz": [
            ("Which of these is primarily a Governance topic?",
             ["Water consumption", "Board independence", "Employee training hours", "Scope 1 emissions"], 1,
             "Board structure and independence sit under Governance."),
            ("Double materiality considers…",
             ["Only financial risks to the company", "Only the company's impacts on society",
              "Both financial materiality and impact materiality", "Two consecutive reporting years"], 2,
             "A topic is material if it is material from either the financial or the impact perspective."),
            ("Which standard is designed mainly for reporting an organisation's impacts on people and the planet?",
             ["GRI Standards", "IFRS S2", "A balance sheet", "ISO 9001"], 0, None),
        ],
    },
    {
        "course": dict(
            title="GHG Accounting: Scope 1, 2 and 3",
            subtitle="Build a corporate greenhouse gas inventory using the GHG Protocol",
            description=(
                "A practitioner's course on measuring a company's carbon footprint. Set boundaries, classify "
                "emissions into scopes, apply emission factors and avoid the most common inventory mistakes."
            ),
            learning_outcomes=(
                "Set organisational and operational boundaries\n"
                "Classify emissions into Scope 1, 2 and 3\n"
                "Report Scope 2 using location-based and market-based methods\n"
                "Calculate emissions from activity data and emission factors"
            ),
            category="Carbon Accounting", level="Intermediate", duration_hours=4, price=4999,
        ),
        "modules": [
            ("The GHG Protocol and inventory boundaries", "Article", """
The **GHG Protocol Corporate Standard** is the most widely used framework for corporate emissions inventories.
It covers the seven Kyoto gases: CO₂, CH₄, N₂O, HFCs, PFCs, SF₆ and NF₃, reported together as **CO₂-equivalent
(CO₂e)** using Global Warming Potentials.

**Organisational boundary** – choose one consolidation approach and apply it consistently:
- *Equity share* – account for emissions in proportion to ownership.
- *Financial control* – 100% of operations over which you have financial control.
- *Operational control* – 100% of operations whose operating policies you control.

**Operational boundary** – decide which emission sources (scopes) to include for those operations.
"""),
            ("Scopes 1, 2 and 3 explained", "Article", """
- **Scope 1 – direct emissions** from sources the company owns or controls: fuel burned in boilers, generators
  and vehicles, process emissions, refrigerant leaks.
- **Scope 2 – indirect emissions from purchased energy**: electricity, steam, heat and cooling. Report both the
  **location-based** method (average grid factors) and the **market-based** method (contractual instruments such
  as renewable energy certificates and supplier-specific factors).
- **Scope 3 – all other indirect value-chain emissions**, in **15 categories**: 8 upstream (e.g. purchased goods
  and services, business travel, employee commuting) and 7 downstream (e.g. use of sold products, end-of-life
  treatment, investments). For many companies Scope 3 is the largest share of the footprint.
"""),
            ("Calculating emissions", "Article", """
The core formula is:

> **Emissions = Activity data × Emission factor**

*Illustrative example:* a site uses 10,000 kWh of grid electricity. With a grid emission factor of
0.7 kg CO₂e/kWh, location-based Scope 2 emissions are 10,000 × 0.7 = 7,000 kg = **7 t CO₂e**.
(Always use the current official factor for the relevant grid and year.)

**Good practice:** document data sources and assumptions, prefer primary data over spend-based estimates where
material, keep a consistent base year, and recalculate the base year after significant structural changes.
"""),
            ("Knowledge check: GHG accounting", "Quiz", ""),
        ],
        "quiz": [
            ("Diesel burned in a company-owned generator is reported as…",
             ["Scope 1", "Scope 2", "Scope 3", "Not reported"], 0, "It is a direct emission from an owned source."),
            ("How many Scope 3 categories does the GHG Protocol define?", ["5", "8", "12", "15"], 3,
             "15 categories: 8 upstream and 7 downstream."),
            ("Which Scope 2 method reflects renewable energy certificates a company has purchased?",
             ["Location-based", "Market-based", "Equity share", "Spend-based"], 1, None),
            ("A site uses 20,000 kWh with a factor of 0.5 kg CO₂e/kWh. What are its emissions?",
             ["1 t CO₂e", "10 t CO₂e", "40 t CO₂e", "100 t CO₂e"], 1, "20,000 × 0.5 = 10,000 kg = 10 t CO₂e."),
        ],
    },
    {
        "course": dict(
            title="BRSR Reporting for Indian Companies",
            subtitle="Prepare a Business Responsibility and Sustainability Report with confidence",
            description=(
                "A guided walkthrough of SEBI's BRSR format: who must report, how the report is structured, the "
                "nine NGRBC principles, and how BRSR Core and assurance change data expectations."
            ),
            learning_outcomes=(
                "Identify which companies must file a BRSR\n"
                "Navigate Sections A, B and C of the format\n"
                "Map disclosures to the nine NGRBC principles\n"
                "Prepare data for BRSR Core assurance"
            ),
            category="Sustainability Reporting", level="Intermediate", duration_hours=3, price=3999,
        ),
        "modules": [
            ("BRSR at a glance", "Article", """
The **Business Responsibility and Sustainability Report (BRSR)** was introduced by SEBI in 2021, replacing the
earlier Business Responsibility Report. It is mandatory for the **top 1,000 listed companies by market
capitalisation** (from FY 2022-23) and can be adopted voluntarily by others.

The report has three sections:
- **Section A – General disclosures**: company details, products and operations, employees, CSR, transparency.
- **Section B – Management and process disclosures**: policies, governance and oversight for each principle.
- **Section C – Principle-wise performance**: *Essential* indicators (mandatory) and *Leadership* indicators
  (voluntary) for each principle.

Always check the latest SEBI circulars for current scope and timelines.
"""),
            ("The nine NGRBC principles", "Article", """
Section C is organised around the **National Guidelines on Responsible Business Conduct (NGRBC)**:

1. Ethics, transparency and accountability
2. Safe and sustainable goods and services
3. Employee well-being
4. Stakeholder responsiveness
5. Human rights
6. Protecting and restoring the environment
7. Responsible and transparent public policy advocacy
8. Inclusive growth and equitable development
9. Responsible engagement with consumers
"""),
            ("BRSR Core and assurance", "Article", """
**BRSR Core** is a subset of key performance indicators, such as GHG emissions, water, energy, waste,
employee well-being and gender diversity, for which SEBI requires **reasonable assurance**, phased in starting
with the largest listed companies by market capitalisation.

Getting ready for assurance:
- Define each KPI's boundary and calculation methodology in writing.
- Keep an audit trail from source documents (bills, meter readings, HR records) to reported numbers.
- Assign data owners and introduce maker-checker reviews.
- Run a dry-run internal review before the external assurance engagement.
"""),
            ("Knowledge check: BRSR", "Quiz", ""),
        ],
        "quiz": [
            ("Which regulator mandates the BRSR?", ["RBI", "SEBI", "MCA", "CPCB"], 1, None),
            ("How many NGRBC principles structure Section C of the BRSR?", ["5", "7", "9", "17"], 2, None),
            ("In Section C, which indicators are mandatory?",
             ["Leadership indicators", "Essential indicators", "Both", "Neither"], 1,
             "Essential indicators are mandatory; leadership indicators are voluntary."),
        ],
    },
    {
        "course": dict(
            title="Net Zero Strategy and Science-Based Targets",
            subtitle="Design a credible corporate decarbonisation pathway",
            description=(
                "For sustainability leads and executives building a climate strategy: what net zero really "
                "means, how science-based targets are set, and how to turn targets into a funded transition plan."
            ),
            learning_outcomes=(
                "Explain net zero in line with the Paris Agreement\n"
                "Distinguish near-term and long-term science-based targets\n"
                "Use abatement levers and cost curves to prioritise action\n"
                "Position carbon credits correctly within a net-zero strategy"
            ),
            category="Climate Strategy & Net Zero", level="Advanced", duration_hours=4, price=5999,
        ),
        "modules": [
            ("What net zero means", "Article", """
The **Paris Agreement** aims to hold warming well below 2 °C and pursue efforts to limit it to 1.5 °C.
Pathways consistent with 1.5 °C reach **global net-zero CO₂ around mid-century**.

For a company, a credible net-zero commitment means:
- **Deep decarbonisation** of its own operations and value chain (Scopes 1, 2 and 3) in line with science.
- **Neutralising** only the hard-to-abate residual emissions with permanent carbon removals.
- **Interim targets** and transparent annual progress reporting, not just a distant end date.
"""),
            ("Science-based targets", "Article", """
The **Science Based Targets initiative (SBTi)** validates corporate targets against climate science.
Under its Corporate Net-Zero Standard:
- **Near-term targets** cover roughly 5–10 years and roughly halve emissions by around 2030 for most sectors.
- **Long-term targets** require deep reductions, around 90% for most companies, by 2050 at the latest.
- Carbon credits **do not count** towards meeting reduction targets; they can support *beyond value chain
  mitigation*.

Check the SBTi's current criteria and sector guidance before setting targets, as they are updated periodically.
"""),
            ("From targets to a transition plan", "Article", """
1. **Baseline** – a complete, assured GHG inventory.
2. **Levers** – energy efficiency, electrification, renewable electricity (on-site, PPAs), low-carbon fuels,
   process change, supplier engagement, product redesign.
3. **Prioritise** – a marginal abatement cost curve (MACC) compares the cost per tonne and the volume of each
   lever.
4. **Fund and govern** – put capex in the budget, use an internal carbon price, and link targets to leadership KPIs.
5. **Disclose** – report progress annually, aligned with ISSB / TCFD-style transition planning disclosures.
"""),
            ("Knowledge check: net zero", "Quiz", ""),
        ],
        "quiz": [
            ("Under the SBTi Net-Zero Standard, carbon credits can be used to…",
             ["Meet near-term reduction targets", "Replace Scope 3 reductions",
              "Support beyond value chain mitigation", "Avoid setting targets"], 2, None),
            ("A marginal abatement cost curve helps a company…",
             ["Calculate Scope 2 emissions", "Prioritise reduction levers by cost and volume",
              "Choose a consolidation approach", "File its BRSR"], 1, None),
            ("Residual emissions at net zero should be neutralised with…",
             ["Avoided-emission credits", "Permanent carbon removals", "Renewable energy certificates",
              "Nothing"], 1, None),
        ],
    },
]


def load_starter_courses():
    """Create the starter courses as unpublished drafts. Returns the number of courses created."""
    existing = {c["title"] for c in db.list_courses(published_only=False)}
    created = 0
    for spec in STARTER_COURSES:
        if spec["course"]["title"] in existing:
            continue
        course_id = db.create_course(**spec["course"], instructor=INSTRUCTOR, is_published=0)
        for title, mtype, content in spec["modules"]:
            module_id = db.create_module(course_id, title, mtype, content=content.strip())
            if mtype == "Quiz":
                for question, options, correct, explanation in spec["quiz"]:
                    db.add_question(module_id, question, options, correct, explanation or "")
        created += 1
    return created
