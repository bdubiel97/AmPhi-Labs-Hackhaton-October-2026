---
description: Definition of done for the current milestone: run the app checks from the requirements file
allowed-tools: Bash, Read, Grep, Glob
---

Check the current milestone against `requirements.md`. Milestone or extra context: $ARGUMENTS

1. Start the app the way section 8 describes (for example `streamlit run app.py`) and confirm it starts without errors. Stop it again afterwards.
2. Go through every item in section 11 (acceptance criteria) that applies to this milestone (section 14). Check each one by running code or the app, not by reading the source. Report pass or fail per item, with the command you used.
3. For each item, name the requirement number (section 4) or decision (D-xx, section 6) it proves.
4. Check the restrictions in section 12: no new library, no extra file, no external call beyond what is listed.
5. List any assumption you relied on that is not yet in section 5, and propose it as a new Q-entry in the section 5 format (impact, owner, status, working assumption). Don't add it yourself.

If a check fails: fix it, then run the check again. Don't report a failure and move on.
If nothing in this milestone is tested, the milestone is not done.
Don't change `requirements.md` and don't commit without being asked.
