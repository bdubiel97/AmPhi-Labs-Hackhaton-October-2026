
---

## 1. Project description

Within this project, we would like to build a product that helps with the sorting recybility efficiency. The current problem is only 10% of flexible packacking is recyble, because its cheap and the easiest to handle. As of now its cheaper to not recycle it (more time conduming as well as resources consuming). Our base goal it recycle more for the same price and propose alternative materials and packaging, so that with this tool we can obtain more than 10% recibility.

Example:

> Brand X sells dry snacks in a PET/PE multilayer pouch and wants to switch to a fibre-based pack. The packaging team doesn't know which paper and barrier coating combinations protect the product long enough and are still recyclable in the paper stream. The app takes the product's protection needs and ranks candidate fibre materials from the dossier on barrier fit, recyclability and cost, then explains the top choice in plain language.

Throughout the beginning part of the project, we have collected relevant information on the context of the actual project from the domain experts. I will give that context here:

Interview with:

Notes:

- Less layers are better in the context of the recycling feasibility
- Economic factor plays a role (especially for smaller company), to introduce more sustainable material
- Automation from the mechanical point of view (sustain efficiency of the line without chaning it too much) is also important
- Convenience from the point of view of the user (e.g. easy opening)

Challengers:

- Machinability (automation maintenance speed)
- Material performance
- Product shelf-life
- >> Recycibility
- Budget costs
- Packacking usage
- Quantity of material

Video:

- can AI propose barrier/threshold for paper wrap? 

Which 

## 2. Users and demo scenario

User: will be brand owners and they need to see benefit in that.

Instruction: brand owner should access to this tool and see tangible benefit from different packcing based on their inquire. 

Demo path:

1. Owner provide us/upload product image along with the material specifications that are hard to recycle.
2. It should be able in input features from a list with a drop-down menu product name, destination. Depending of the input feature, it should be a drop-down meanu or fillable text
3. Analyse given product and suggest alternative packcing/material which is the most optimal
4. User should be able to indicate which factors are important for this product (by ):
	1. cost efficiency
	2. environmental trade-offs
	3. local recycling rules
	4. destination market 
	5. product protection
5. After confirming the product features, it outputs window with the output analysis
## 3. Input data

Inputs data:

> Pop-up window with entries to be filled by user which product he wants to 
>
> | Column       | Meaning                                        | Unit           |
> |-----------  |-------------------------------- |-----------|
> | material_id | identifier.                                       | text            |
> | name           | trade name                                   | text            |
> | grammage  | weight                                           | g/m2          |
> | otr                | oxygen transmission rate           | cc/m2/day |
> | wvtr             | water vapour transmission rate | g/m2/day   |
> | coating        | coating type                                 | text            |
> | fibre_share | fibre content                                 | %               |
> | price            | price                                              | EUR/kg      |
> | geometry of the product | dimensions of the given product | mm|
> | current material | descirption what kind of material is used now | text |
> |packcing condition after use | description of the packcing after is used | text |
> | general requierments | generic description what user actuallly expects | text |
> | technical drawings | sheets with dimensions and 3D | pdf's|

Reference data (artificial, D-01), in `data/`:

- `materials.csv`, 15 rows: `material_id`, `name`, `format` (tube or film), `structure`, `layers`, `recycling_stream`, `recyclability_pct` (%), `otr` (cc/m2/day), `wvtr` (g/m2/day), `price_eur_kg` (EUR/kg), `co2_kg_per_kg` (kg CO2e per kg), `machinability_1to5`, `notes`, `mass_factor` (× current pack mass, D-07)
- `products.csv`, 5 rows: `product_id`, `name`, `format`, `current_material_id`, `shelf_life_days`, `max_otr` (cc/m2/day), `max_wvtr` (g/m2/day), `annual_volume_units`, `pack_mass_g` (g)
- `country_rules.csv`, 7 rows: `country`, `rule`, `fee_eur_per_tonne` (base EUR per tonne, modulated by grade band, D-08), `source_url`


## 4. Requirements

1. The app must be clear for the user, meaning that they are able easily fill-in product features.
2. We should give an user at least few proposal
3. Output should be a descriptive reasoning (advice) produced by connected LLM agent
4. Another output, should be some cost analysis output of LLM
5. For information given in terms of local taxes/regulations/etc. user should have possibility to click directly to the source
6. User should see the impact that this decision will create
7. User should always see the alternative of different material/type of packing

Nice to have:

1. One tab with a demo usage (animation of video explaining how to fill in the tab)

## 5. Assumptions and open questions

1. Clear images will be provided by the user
2. 

Q-1: Where does the reference data on materials and packaging come from?
- Impact: High: the alternatives, scores and cost-benefit all depend on it
- Owner: Team
- Status: Answered (D-01)
- Working assumption: artificial data, labelled "illustrative" in the app

Q-2: Which official sources do the country rule links point to?
- Impact: Medium: requirement 5
- Owner: Team
- Status: Open
- Working assumption: links to official pages (EU packaging regulation, plus the national rules for NL and DE), shown as "to verify" until the team checks them

Q-3: What does the app do with the uploaded product image?
- Impact: Medium: demo step 1
- Owner: Team
- Status: Open
- Working assumption: the image goes to Claude, which describes the current packaging and pre-fills the text fields; the user can still edit them

Q-4: Does an alternative pack weigh the same as the current one?
- Impact: Medium: changes the yearly cost and CO2 figures
- Owner: Team
- Status: Answered (D-07)
- Working assumption: no, each material has its own weight factor

Q-5: How is the country fee applied?
- Impact: Medium: drives the "destination market" score and the cost-benefit
- Owner: Team
- Status: Answered (D-08)
- Working assumption: grade bands by recyclability

## 6. Decisions

**D-01: Reference data is artificial and labelled "illustrative"**
Decided: Claude creates CSV files of hard-to-recycle plastic packs and their alternatives; the app shows an "illustrative data" note.
Why: no dataset from the organisers is available and time is short (Q-1).
Rejected: an organiser or dossier file (none exists); a hand-built CSV from the expert interviews (too slow).
Affects: section 3, section 7, the data files.

**D-02: The demo uses a toothpaste tube and a dirty food foil**
Decided: both are preset products in the data; the demo path in section 2 runs on the toothpaste tube.
Why: both are typical multi-plastic or contaminated packs that are hard to recycle.
Rejected: no preset, where the user types everything (risky in a live demo).
Affects: section 2, the data files.

**D-03: Alternatives are ranked with a rule-based weighted score, not ML**
Decided: each alternative gets a 0–100 score; the weights come from the user's five importance factors (cost, environment, local rules, destination market, protection); the result always includes a cost-benefit.
Why: artificial data gives no real ground truth to train on, and the jury must be able to follow the score.
Rejected: an ML model in scikit-learn (no real training data, hard to explain in a pitch).
Affects: section 7, section 4.

**D-04: The main file is `app.py`**
Decided: the app starts with `streamlit run app.py`.
Why: it matches section 11.
Rejected: `main.py` (only in the template example).
Affects: section 8, section 11.

**D-05: No milestones; build in one pass, then run `/dod`**
Decided: the whole app is built at once, then checked against section 11.
Why: there's no time for time-boxed milestones (section 14).
Rejected: milestones as described in `CLAUDE.md` (no time).
Affects: section 14; this overrides the milestone rule in `CLAUDE.md` for this project.

**D-06: Stack is Streamlit, Python 3.13 in `.venv`, pandas, Plotly and the anthropic SDK**
Decided: only what's already installed in `.venv`; the API key comes from `.streamlit/secrets.toml`; the model is Claude Sonnet 5.5, for speed; every LLM call has a fallback text, so the demo survives an API failure.
Why: section 8 says "Streamlit, whatever is fastest", and all of these are already installed.
Rejected: other frameworks (the team chose Streamlit); new libraries (not needed).
Affects: section 8.

**D-07: Each material has a weight factor relative to the current pack**
Decided: new column `mass_factor` in `materials.csv` (illustrative, for example aluminium tube 1.3, mono-PE film 0.9, ABL tube 1.0); pack mass = product mass × alternative factor ÷ current material factor.
Why: alternatives can weigh differently, which changes cost and CO2 (Q-4).
Rejected: the same weight for all materials (flatters heavy options); the user enters the weight (slows the demo).
Affects: section 3, `data/materials.csv`, `app.py`.

**D-08: The country fee is applied in grade bands by recyclability**
Decided: recyclability ≥70% pays 0.5× the fee, 30–70% pays 1×, and under 30% pays 2×.
Why: closer to eco-modulated EPR fees and the PPWR grades, and it shows a clear benefit from switching (Q-5).
Rejected: fee × the non-recyclable share (smooth but less realistic); a flat fee (no benefit from switching).
Affects: section 3, `app.py`, the "How the score is built" text in the app.

**D-09: The headline numbers follow the alternative clicked in the table**
Decided: clicking a row in the ranking table updates the four headline numbers (alternatives found, recyclability, yearly cost, recycled and CO2) to that option versus the current pack; with nothing selected they show the top-scored option. The AI advice stays on the top recommendation.
Why: the user wants to compare any alternative, not only the best one.
Rejected: a separate dropdown to pick the alternative (one more control); regenerating the AI advice on every click (slow, costs an API call each time).
Affects: section 9, `app.py`.
> Revision (D-09): the AI advice also follows the clicked alternative; it is generated on the first click (about 6–10 seconds) and cached per option, so clicking back is instant.

Instruction: every choice the team makes during the day gets a number, so nobody reopens it at 14:30. Write the decision so someone else can check it, and always fill in the rejected alternatives, even when the rejection seems obvious. To change a decision, add a revision line on top; don't rewrite it. Claude proposes options with a one-line reason but does not decide for the team.

Flow: write down any decisions already made before saying "requirements.md is filled in"; anything else can stay empty. During the build, tell Claude a choice in plain words (or pick one of its options), and Claude proposes the D-xx entry and writes it after your approval; a later change becomes a revision line.

Decisions made on the start: (fill in the number here + describe below). If none, that's okay at the start of the project build, can be added throughout the project build.

Template:

> **D-01: (the decision, not the topic)**
> Decided: what now applies.
> Why: one or two sentences, with the question number it answers if any.
> Rejected: each alternative that was on the table, with the reason.
> Affects: sections or files that change because of this.

Example:

> **D-01: All code goes in one file, `app.py`**
> Decided: the whole app lives in a single file called `app.py`.
> Why: one file is easy for everyone on the team to find and read.
> Rejected: a separate file per feature (too much to keep track of in one day).
> Affects: section 8, section 12.
>  > Revision (D-01): he whole app lives in a single file called `main.py` because we like it that way more.

## 7. AI and model approach

LLM agent, should be used to convert input data into tangible format which we can cross-reference with the data base of different product already exisiting on the market (also this existing products should be transferred to a tangible data).

LLM should also provide text explanation of the proposed solutions.

For the comparison between alternatives, we should have a standard ML approach that makes comparison between alternative products and packcing. The end equation, should always output cost benefit.
## 8. Tech stack and environment

Up to you whatever is fastest and tangible. Let's keep it in the streamlit.

## 9. Output and interface

Instruction: describe each screen or section, what it shows and where. Mention charts, tables and any text the jury must see. A rough sketch in words is enough.

Base side, this nice overview page displaying the demo. Then it should have interface (button or navigation tab), which navigates you to the analaysis of the new product.

## 10. End goal

End goal: it is given in the points above.

Judging criterion:

#### Problem understanding · 30 points

Does the team understand the real packaging problem they are trying to solve?

1. Vague, no real interviews
2. Some insight, limited evidence
3. Clear problem and some evidence
4. Well defined, credible evidence
5. Deep understanding, strong evidence

#### Impact · 30 points

How much better could this solution make packaging over its full life cycle?

1. Minimal or unclear benefit
2. Some benefit, major gaps
3. Moderate benefit, reasonable plan
4. Strong benefit, clear life-cycle thinking
5. Very high benefit, scalable and credible

#### Creativity & innovation · 15 points

How thoughtfully does the team approach the problem?

1. Not original, repeats existing ideas
2. Some originality, limited differentiation
3. Fresh approach, solves the problem
4. Well thought out, clear advantages
5. Highly innovative, truly distinctive

#### Feasibility & implementation · 10 points

Could this solution realistically work outside the hackathon?

1. Not practical, major barriers
2. Some feasibility, significant gaps
3. Reasonable plan, with some validation
4. Clear path to scale, manageable risks
5. Highly feasible, ready for real-world use

## 11. Acceptance criteria (definition of done)


 - `streamlit run app.py` starts without errors on a fresh start.
 - Every product  returns at least one alternative materia and type of packcing
 - For every product we should have LLM explanation

## 12. Restrictions

NONE

## 13. Out of scope

You can be creative but remember about the goals, descriptive explanation, financial benefits, and configurability.

## 14. Timeline and milestones

Need to be finished basically now.
## 15. Working agreement with Claude (optional)

