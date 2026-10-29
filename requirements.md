
---

## 1. Project description

Instruction: two to five sentences. State the problem, who has it and what the app does about it. Name the challenge or brand if there is one. Avoid general goals ("help sustainability"); describe the one thing the app does.

Example:

> Brand X sells dry snacks in a PET/PE multilayer pouch and wants to switch to a fibre-based pack. The packaging team doesn't know which paper and barrier coating combinations protect the product long enough and are still recyclable in the paper stream. The app takes the product's protection needs and ranks candidate fibre materials from the dossier on barrier fit, recyclability and cost, then explains the top choice in plain language.

## 2. Users and demo scenario

Instruction: who uses the app and the exact steps shown in the pitch. Write the demo as a numbered click path. This decides which screens get built first; anything not in the demo is lower priority.

Example:

> User: packaging engineer at the brand.
>
> Demo path:
> 1. Select product "Salted crackers 200 g" from a dropdown (or enter shelf life and oxygen/moisture sensitivity).
> 2. Click "Find materials".
> 3. See a ranked table of 5 materials with scores and a bar chart.
> 4. Click the top material to read a short AI explanation of why it fits and what the risks are.

## 3. Input data

Instruction: list every file or source with its format, size, and the columns or fields that matter. Paste the first 3 to 5 rows or attach the file. Note units, missing values and anything you know is wrong. Without real column names Claude has to guess, which is the main cause of broken code. 

If possible, I will attach the data in the repository root or hand it in during the conversation.

Example:

> `materials.csv`, 40 rows, one per material:
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
>
> `products.csv`, 6 rows: product_id, name, shelf_life_days, max_otr, max_wvtr.
>
> `recyclability_guideline.pdf`, 12 pages of text with the fibre content and coating rules for paper recycling.
>
> Known issues: `otr` is empty for 7 materials; `price` is missing for 3.



## 4. Requirements

Instruction: what the app must do, as a numbered list of testable statements ("the app shows X when Y"). Split into must-have (needed for the demo) and nice-to-have (only if time is left). Keep must-haves to 3 to 6 items.

Example:

> Must-have:
> 1. Load both CSV files at startup and show an error message if a file or column is missing.
> 2. The user selects a product; the app filters out materials whose `otr` or `wvtr` exceeds the product limits.
> 3. Remaining materials get a score from 0 to 100 (weights: barrier 40, recyclability 40, price 20) and are shown in a sorted table and a bar chart.
> 4. Recyclability is checked against the rules in the guideline (fibre share and coating type), extracted once by the LLM into a JSON rule list.
> 5. Clicking a material shows a 3 to 5 sentence LLM explanation based only on that material's data and the scores.
>
> Nice-to-have:
> 6. Sliders to change the score weights.
> 7. Download the ranking as CSV.

## 5. Assumptions and open questions

Instruction: one numbered list, sorted by impact (what blocks the most work goes first), not by order of discovery. Every question names who answers it. Claude adds its own assumptions here too, so they can be corrected early. An empty answer is fine; an invented one is not.

Statuses: Open, Partly answered, Answered (D-xx), Waiting on (name).

Example:

> Q1: At what conditions are the `otr` values measured? 
> - Impact: High: decides the barrier filter 
> - Owner: Materials expert at the booth 
> - Status: Waiting on expert 
> - Working assumption: 23 C, 50% RH. If wrong, the filter limits shift and the ranking changes 

> Q2: Does the brand want price in the score?
> - Impact: Medium: changes the weights
> - Owner: Challenge owner
> - Status: Open 
> - Working assumption: Yes, weight 20


## 6. Decisions

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

Instruction: state which part is computed (rules, ML, optimisation) and which part uses an LLM, and for what. Name the model provider if it is fixed. If unsure, write the data type and let Claude propose and discuss with a team.

Example:

> Task (id) explain task it needs to tackle (can be more then one)
> Proposed approach (id): standard ML approach (team can list a specific model)/LLM/Not sure

## 8. Tech stack and environment

Instruction: framework, Python version, libraries allowed, where it runs and how secrets are stored. Mention the operating system, since commands differ. The app format (web app, desktop executable, mobile app, etc.) also belongs here. Anything not chosen yet stays "to fill in" and becomes a decision (D-xx) once the team picks it.

Example:

> Streamlit, Python 3.11, pandas, Plotly, pypdf, anthropic SDK.
> Runs locally on a Windows 11 laptop with `streamlit run app.py`, from the project folder, in a virtual environment `.venv`.
> API key in `.streamlit/secrets.toml` as `ANTHROPIC_API_KEY`; this file is never shared or committed.

## 9. Output and interface

Instruction: describe each screen or section, what it shows and where. Mention charts, tables and any text the jury must see. A rough sketch in words is enough.

Example:

> One page, wide layout.
> Sidebar: product dropdown, "Find materials" button.
> Main area, top: 3 metrics (materials tested, materials passing, best score).
> Main area, middle: ranked table and horizontal bar chart side by side.
> Main area, bottom: expander per material with the AI explanation.
> Title: "Fibre Swap Finder". Green theme.

## 10. End goal

Instruction: what exists at the end and how it will be judged. Include the deliverables and the deadline. This tells Claude what to optimise for (a stable demo, not complete features).

Example:

> A working local app that runs the demo path from section 2 without errors, on the real dossier data.
> Deliverables: the app, a 2-minute pitch video with 5 slides, submitted by 15:45.
> The jury should see real numbers from the data and one clear recommendation.

## 11. Acceptance criteria (definition of done)

Instruction: a checklist to confirm the app is ready. Each item is checked by running the app. Claude uses this to test its own work before handing it over, through the `/dod` command (`.claude/commands/dod.md`) at every milestone in section 14. For each item, name the decision (D-xx) or requirement number it proves.

Example:

> - `streamlit run app.py` starts without errors on a fresh start.
> - Every product in `products.csv` returns at least one ranked material, or a clear "no material fits" message.
> - Materials with missing `otr` are shown as "no data", not as a crash or a zero.
> - The app still works with the internet off (fallback explanation shown).
> - The full demo path takes under 60 seconds.

## 12. Restrictions

Instruction: anything Claude must not do or use: libraries, services, data handling, things that would break the demo. Include confidentiality rules from the organisers or brand.

Example:

> - No external data beyond the dossier; no web scraping.
> - Dossier data must not be uploaded anywhere except the one LLM API call.
> - No user login, no database server (CSV files and SQLite only).
> - No new library added without asking first.
> - Keep everything in at most 3 Python files so it stays readable.

## 13. Out of scope

Instruction: features that look related but will not be built. This stops the scope from growing during the day.

Example:

> Shelf-life simulation, line speed prediction, cost model beyond EUR/kg, mobile layout, deployment to a public host.

## 14. Timeline and milestones

Instruction: time boxes for the build, with what must work at each point. If a milestone is missed, cut nice-to-haves, not testing.

Example:

> | Time | Milestone |
> |---|---|
> | 13:30 | Requirements filled in, data loaded and checked |
> | 14:00 | Filtering and scoring work, table visible |
> | 14:30 | Chart and LLM explanation work |
> | 15:00 | Acceptance criteria checked, fallback tested |
> | 15:15 | Code frozen, record pitch video |
> | 15:45 | Submission |
## 15. Working agreement with Claude (optional)

Instruction: how the build should proceed, for example step by step, file by file, or with a test after each step.

Example:

> Build in the order of the milestones. After each milestone, give the command to run and wait for confirmation before continuing. When changing existing code, show which file and the lines around the change. Ask before deleting or renaming files.
