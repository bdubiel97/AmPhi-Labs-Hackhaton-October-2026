"""Pack Swap Advisor: suggests more recyclable packaging for hard-to-recycle plastic packs.

Run with: streamlit run app.py
"""

import base64
import io
import json
from pathlib import Path

import anthropic
import pandas as pd
import plotly.express as px
import streamlit as st
from pypdf import PdfReader

DATA_DIR = Path(__file__).parent / "data"
MODEL = "claude-sonnet-5-5"  # D-06

REQUIRED_COLUMNS = {
    "materials.csv": [
        "material_id", "name", "format", "structure", "layers", "recycling_stream",
        "recyclability_pct", "otr", "wvtr", "price_eur_kg", "co2_kg_per_kg",
        "machinability_1to5", "notes", "mass_factor",
    ],
    "products.csv": [
        "product_id", "name", "format", "current_material_id", "shelf_life_days",
        "max_otr", "max_wvtr", "annual_volume_units", "pack_mass_g",
    ],
    "country_rules.csv": ["country", "rule", "fee_eur_per_tonne", "source_url"],
}

# The five importance factors from the demo path (section 2, step 4), D-03
FACTORS = {
    "cost": "Cost efficiency",
    "environment": "Environmental trade-offs",
    "local_rules": "Local recycling rules",
    "market": "Destination market",
    "protection": "Product protection",
}


# ---------- Data ----------

def load_data():
    """Load the three CSVs; return (materials, products, rules, errors)."""
    frames, errors = {}, []
    for file, columns in REQUIRED_COLUMNS.items():
        path = DATA_DIR / file
        if not path.exists():
            errors.append(f"Missing file: data/{file}")
            continue
        df = pd.read_csv(path)
        missing = [c for c in columns if c not in df.columns]
        if missing:
            errors.append(f"data/{file} is missing columns: {', '.join(missing)}")
        frames[file] = df
    return (
        frames.get("materials.csv"),
        frames.get("products.csv"),
        frames.get("country_rules.csv"),
        errors,
    )


# ---------- Scoring (rule-based, D-03) ----------

def _scale(series, higher_is_better):
    """Min-max scale to 0-100; a constant series scores 100."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(100.0, index=series.index)
    scaled = (series - lo) / (hi - lo) * 100
    return scaled if higher_is_better else 100 - scaled


def fee_multiplier(recyclability_pct):
    """Grade bands for the country fee (D-08)."""
    if recyclability_pct >= 70:
        return 0.5
    if recyclability_pct >= 30:
        return 1.0
    return 2.0


def rank_alternatives(product, materials, fee_eur_per_tonne, weights):
    """Score the current material and every alternative that meets the barrier limits.

    product: dict with format, current_material_id, max_otr, max_wvtr,
             annual_volume_units, pack_mass_g.
    Returns a DataFrame sorted by score, current material included as baseline.
    """
    candidates = materials[materials["format"] == product["format"]].copy()
    current_id = product["current_material_id"]
    fits = (candidates["otr"] <= product["max_otr"]) & (candidates["wvtr"] <= product["max_wvtr"])
    candidates = candidates[fits | (candidates["material_id"] == current_id)].copy()
    candidates["is_current"] = candidates["material_id"] == current_id

    # Cost-benefit per year; pack mass scales with the material's weight factor (D-07)
    current_factor = materials.set_index("material_id").loc[current_id, "mass_factor"]
    annual_kg = (
        product["annual_volume_units"] * product["pack_mass_g"] / 1000
        * candidates["mass_factor"] / current_factor
    )
    candidates["annual_kg"] = annual_kg
    candidates["annual_material_cost_eur"] = annual_kg * candidates["price_eur_kg"]
    candidates["fee_multiplier"] = candidates["recyclability_pct"].apply(fee_multiplier)
    candidates["annual_epr_fee_eur"] = annual_kg / 1000 * fee_eur_per_tonne * candidates["fee_multiplier"]
    candidates["annual_total_cost_eur"] = (
        candidates["annual_material_cost_eur"] + candidates["annual_epr_fee_eur"]
    )
    candidates["annual_co2_t"] = annual_kg * candidates["co2_kg_per_kg"] / 1000
    candidates["annual_recycled_t"] = annual_kg * candidates["recyclability_pct"] / 100 / 1000

    current = candidates[candidates["is_current"]].iloc[0]
    candidates["saving_vs_current_eur"] = current["annual_total_cost_eur"] - candidates["annual_total_cost_eur"]
    candidates["co2_change_t"] = candidates["annual_co2_t"] - current["annual_co2_t"]
    candidates["extra_recycled_t"] = candidates["annual_recycled_t"] - current["annual_recycled_t"]

    # Sub-scores 0-100
    sub = pd.DataFrame(index=candidates.index)
    sub["cost"] = _scale(candidates["annual_total_cost_eur"], higher_is_better=False)
    sub["environment"] = (
        _scale(candidates["co2_kg_per_kg"], higher_is_better=False) * 0.7
        + _scale(candidates["layers"], higher_is_better=False) * 0.3
    )
    sub["local_rules"] = candidates["recyclability_pct"].astype(float)
    sub["market"] = _scale(candidates["annual_epr_fee_eur"], higher_is_better=False)
    barrier_use = (
        candidates["otr"] / product["max_otr"] + candidates["wvtr"] / product["max_wvtr"]
    ) / 2
    sub["protection"] = ((1 - barrier_use) * 100).clip(0, 100)

    total_weight = sum(weights.values()) or 1
    candidates["score"] = sum(sub[f] * w for f, w in weights.items()) / total_weight
    for f in FACTORS:
        candidates[f"score_{f}"] = sub[f].round(0)
    candidates["score"] = candidates["score"].round(1)
    return candidates.sort_values("score", ascending=False).reset_index(drop=True)


# ---------- LLM (D-06): every call has a fallback ----------

def _client():
    try:
        return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        return None


def ask_llm(content, effort="low", max_tokens=4000):
    """Send one message to Claude; return the text, or None on any failure."""
    client = _client()
    if client is None:
        return None
    try:
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            output_config={"effort": effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": content}],
        )
    except (anthropic.APIStatusError, anthropic.APIConnectionError):
        return None
    if response.stop_reason == "refusal":
        return None
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    return text or None


def describe_image(image_bytes, media_type, materials):
    """Q-3: read the pack photo and map it to the closest material in the data."""
    options = "\n".join(
        f"{r.material_id}: {r.name} ({r.format}, {r.structure})" for r in materials.itertuples()
    )
    prompt = (
        "This is a photo of a product's packaging. Reply with JSON only, no code fences, "
        'with keys "current_material" (one sentence describing the packaging material), '
        '"condition_after_use" (one sentence, e.g. food residue), '
        '"format" ("tube" or "film"), and "closest_material_id" (one id from this list):\n'
        + options
    )
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                     "data": base64.standard_b64encode(image_bytes).decode()}},
        {"type": "text", "text": prompt},
    ]
    text = ask_llm(content, effort="low", max_tokens=2000)
    if not text:
        return None
    try:
        return json.loads(text.strip().removeprefix("```json").removesuffix("```"))
    except json.JSONDecodeError:
        return None


def fallback_advice(product_name, ranked, country, focus_name):
    """Plain advice built from the numbers, used when the LLM is unavailable."""
    current = ranked[ranked["is_current"]].iloc[0]
    alts = ranked[~ranked["is_current"]]
    if alts.empty:
        return f"No alternative in the data meets the barrier needs of {product_name}."
    best = alts[alts["name"] == focus_name].iloc[0]
    rank = alts.index.get_loc(best.name) + 1
    return (
        f"**Option {rank} of {len(alts)}: {best['name']}** ({best['structure']}).\n\n"
        f"It replaces {current['name']} and raises recyclability from "
        f"{current['recyclability_pct']:.0f}% to {best['recyclability_pct']:.0f}% "
        f"({best['recycling_stream']}). For {country}, the yearly cost changes by "
        f"EUR {-best['saving_vs_current_eur']:,.0f} (negative means a saving), CO2 changes by "
        f"{best['co2_change_t']:+.1f} t per year, and {best['extra_recycled_t']:.1f} t more "
        f"packaging can be recycled each year.\n\n"
        f"Check machinability on your line (score {best['machinability_1to5']}/5) and run "
        f"shelf-life tests before switching.\n\n*(Fallback text: the AI explanation was unavailable.)*"
    )


def llm_advice(product, ranked, country_rule, extra_context, focus_name):
    """Requirements 3 and 4: descriptive advice plus cost analysis."""
    cols = [
        "name", "structure", "is_current", "score", "otr", "wvtr", "recyclability_pct",
        "recycling_stream", "machinability_1to5", "mass_factor", "fee_multiplier", "annual_epr_fee_eur",
        "annual_total_cost_eur", "saving_vs_current_eur", "co2_change_t", "extra_recycled_t",
    ]
    table = ranked[cols].round(1).to_csv(index=False)
    prompt = f"""You advise a brand owner on switching to more recyclable packaging.
Use only the data below; it is illustrative demo data. Write in plain language, at most 250 words, in markdown:
Explain the option "{focus_name}" as a replacement for the current pack.
1. A one-line verdict on this option; if it is not the top-scored alternative, say briefly how it compares to the top one.
2. Why it fits this product or not (protection, recyclability, machinability).
3. Cost analysis for this option: yearly cost difference vs the current pack, the EPR fee effect, and CO2 change.
4. Two risks or next steps (e.g. line trials, shelf-life tests).

Product: {product['name']} ({product['format']}), {product['annual_volume_units']:,} units per year,
{product['pack_mass_g']} g per current pack, max OTR {product['max_otr']}, max WVTR {product['max_wvtr']}.
Pack mass differs per material (mass_factor, relative to 1.0).
Destination market rule: {country_rule['country']}: {country_rule['rule']}
(base fee EUR {country_rule['fee_eur_per_tonne']} per tonne; fee_multiplier is 0.5 at 70%+ recyclable,
1.0 at 30-70%, 2.0 below 30%).
User notes: {extra_context or 'none'}

Ranked options (EUR and tonnes per year; positive saving means cheaper than current):
{table}"""
    return ask_llm(prompt, effort="medium", max_tokens=4000)


@st.cache_data(show_spinner=False)
def cached_advice(product_json, ranked_json, rule_json, extra_context, focus_name):
    return llm_advice(
        json.loads(product_json),
        pd.read_json(io.StringIO(ranked_json)),
        json.loads(rule_json),
        extra_context,
        focus_name,
    )


def pdf_text(uploaded):
    try:
        reader = PdfReader(uploaded)
        return " ".join((p.extract_text() or "") for p in reader.pages[:3])[:2000]
    except Exception:
        return ""


# ---------- UI ----------

def overview_tab():
    st.subheader("Only about 10% of flexible plastic packaging gets recycled")
    st.write(
        "Multilayer tubes and dirty foils are cheap and easy to run on a packing line, "
        "so they stay in use, and most of them end up in residual waste. "
        "**Pack Swap Advisor** shows a brand owner which more recyclable pack would work "
        "for their product, what it costs per year, and what it changes for the environment."
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Flexible packaging recycled today", "~10%")
    c2.metric("Factors you can weigh", "5")
    c3.metric("EU deadline for recyclable packs", "2030")
    st.markdown(
        "**How it works**\n"
        "1. Pick a product (or upload a photo of the pack) and the destination market.\n"
        "2. Say which factors matter most: cost, environment, local rules, market, protection.\n"
        "3. Get ranked alternatives, a yearly cost-benefit, and an AI explanation with links to the rules.\n\n"
        "Open the **Analyse a product** tab to start."
    )
    st.info("Demo data: all materials, prices and fees are illustrative, not measured values (D-01).")


def analyse_tab(materials, products, rules):
    st.info("Illustrative data (D-01). Rule links are to official pages but still need checking (Q-2).")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### 1. Product")
        names = products["name"].tolist() + ["Custom product"]
        choice = st.selectbox("Product", names, index=0)
        country = st.selectbox("Destination market", rules["country"].tolist(), index=1)
        image = st.file_uploader("Photo of the current pack (optional)", type=["png", "jpg", "jpeg", "webp"])
        drawing = st.file_uploader("Technical drawing (optional, PDF)", type=["pdf"])

    preset = products[products["name"] == choice].iloc[0].to_dict() if choice != "Custom product" else None

    image_info = None
    if image is not None:
        key = f"img_{image.name}_{image.size}"
        if key not in st.session_state:
            with st.spinner("Reading the photo..."):
                st.session_state[key] = describe_image(image.getvalue(), image.type, materials)
        image_info = st.session_state[key]
        if image_info is None:
            st.warning("Could not read the photo; please fill in the fields by hand.")

    with right:
        st.markdown("#### 2. Product features")
        mat_labels = {r.material_id: f"{r.material_id}: {r.name}" for r in materials.itertuples()}
        default_mat = (image_info or {}).get("closest_material_id") or (preset or {}).get("current_material_id", "M01")
        if default_mat not in mat_labels:
            default_mat = "M01"
        current_id = st.selectbox(
            "Current material", list(mat_labels), index=list(mat_labels).index(default_mat),
            format_func=mat_labels.get,
        )
        fmt = materials.set_index("material_id").loc[current_id, "format"]
        c1, c2 = st.columns(2)
        max_otr = c1.number_input("Max OTR (cc/m2/day)", value=float((preset or {}).get("max_otr", 2.0)), min_value=0.01)
        max_wvtr = c2.number_input("Max WVTR (g/m2/day)", value=float((preset or {}).get("max_wvtr", 1.0)), min_value=0.01)
        volume = c1.number_input("Units per year", value=int((preset or {}).get("annual_volume_units", 1_000_000)), min_value=1, step=100_000)
        mass = c2.number_input("Pack mass (g)", value=float((preset or {}).get("pack_mass_g", 10.0)), min_value=0.1)
        geometry = st.text_input("Geometry (mm)", placeholder="e.g. 35 x 150")
        condition = st.text_input("Pack condition after use", value=(image_info or {}).get("condition_after_use", ""))
        notes = st.text_area("General requirements", value=(image_info or {}).get("current_material", ""), height=80)

    st.markdown("#### 3. What matters most for this product? (0 = ignore, 5 = very important)")
    cols = st.columns(len(FACTORS))
    weights = {f: cols[i].slider(label, 0, 5, 3, key=f"w_{f}") for i, (f, label) in enumerate(FACTORS.items())}

    if st.button("Analyse", type="primary"):
        product = {
            "name": choice if preset else "Custom product",
            "format": fmt, "current_material_id": current_id,
            "max_otr": max_otr, "max_wvtr": max_wvtr,
            "annual_volume_units": int(volume), "pack_mass_g": mass,
        }
        rule = rules[rules["country"] == country].iloc[0].to_dict()
        ranked = rank_alternatives(product, materials, rule["fee_eur_per_tonne"], weights)
        extra = "; ".join(x for x in [
            f"geometry {geometry}" if geometry else "",
            f"condition after use: {condition}" if condition else "",
            notes,
            f"technical drawing text: {pdf_text(drawing)}" if drawing else "",
        ] if x)
        st.session_state["result"] = (product, ranked, rule, extra)
        st.session_state.pop("ranking_table", None)  # new analysis starts with no row selected

    if "result" in st.session_state:
        show_result(*st.session_state["result"])


def show_result(product, ranked, rule, extra):
    st.divider()
    st.markdown(f"### Analysis: {product['name']}")
    alts = ranked[~ranked["is_current"]]
    current = ranked[ranked["is_current"]].iloc[0]
    if alts.empty:
        st.warning("No material in the data meets these barrier needs. Try relaxing the OTR or WVTR limits.")
        return
    # Headline numbers are filled after the table, so they can follow the clicked row (D-09)
    metrics_box = st.container()

    table, chart = st.columns([3, 2])
    with table:
        shown = ranked.assign(option=ranked["name"] + ranked["is_current"].map({True: " (current)", False: ""}))
        event = st.dataframe(
            shown[["option", "score", "structure", "recyclability_pct", "recycling_stream",
                   "machinability_1to5", "annual_total_cost_eur", "saving_vs_current_eur", "co2_change_t"]],
            hide_index=True, width="stretch",
            column_config={
                "option": "Option", "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
                "structure": "Structure", "recyclability_pct": st.column_config.NumberColumn("Recyclable", format="%d%%"),
                "recycling_stream": "Stream", "machinability_1to5": "Machinability (1-5)",
                "annual_total_cost_eur": st.column_config.NumberColumn("Cost/yr (EUR)", format="%,.0f"),
                "saving_vs_current_eur": st.column_config.NumberColumn("Saving/yr (EUR)", format="%,.0f"),
                "co2_change_t": st.column_config.NumberColumn("CO2 change (t/yr)", format="%+.1f"),
            },
            on_select="rerun", selection_mode="single-row", key="ranking_table",
        )

    rows = event.selection.rows
    picked = ranked.iloc[rows[0]] if rows and not ranked.iloc[rows[0]]["is_current"] else alts.iloc[0]
    with metrics_box:
        hint = "" if rows else " Click a row in the table to compare another option."
        st.caption(f"Comparing **{picked['name']}** with the current **{current['name']}**.{hint}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Alternatives found", len(alts))
        m2.metric("Recyclability", f"{picked['recyclability_pct']:.0f}%",
                  f"{picked['recyclability_pct'] - current['recyclability_pct']:+.0f} pts")
        m3.metric("Yearly cost vs today", f"EUR {-picked['saving_vs_current_eur']:+,.0f}",
                  "cheaper" if picked["saving_vs_current_eur"] > 0 else "more expensive",
                  delta_color="normal" if picked["saving_vs_current_eur"] > 0 else "inverse")
        m4.metric("Extra packaging recycled", f"{picked['extra_recycled_t']:.1f} t/yr",
                  f"CO2 {picked['co2_change_t']:+.1f} t/yr", delta_color="off")
    with chart:
        fig = px.bar(
            shown.sort_values("score"), x="score", y="option", orientation="h",
            color="is_current", color_discrete_map={True: "#9aa0a6", False: "#2e7d32"},
            labels={"score": "Score (0-100)", "option": ""}, range_x=[0, 100],
        )
        fig.update_layout(showlegend=False, height=320, margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(fig, width="stretch")

    with st.expander("How the score is built"):
        st.write(
            "Each option gets five sub-scores from 0 to 100, weighted by your sliders: "
            "cost (yearly material cost plus EPR fee), environment (CO2 per kg and number of layers), "
            "local rules (recyclability %), destination market (yearly EPR fee), "
            "and protection (how far the barrier stays below the product's OTR/WVTR limits). "
            "Pack mass changes with each material's weight factor (D-07). The country fee uses grade "
            "bands: 70% or more recyclable pays 0.5× the fee, 30–70% pays 1×, under 30% pays 2× (D-08)."
        )
        st.dataframe(ranked[["name"] + [f"score_{f}" for f in FACTORS]], hide_index=True, width="stretch")

    # The advice follows the clicked option and is cached per option (D-09 revision)
    st.markdown(f"#### AI advice: {picked['name']}")
    with st.spinner("Writing the advice..."):
        advice = cached_advice(
            json.dumps(product), ranked.to_json(), json.dumps(rule, default=str), extra, picked["name"],
        )
    st.markdown(advice or fallback_advice(product["name"], ranked, rule["country"], picked["name"]))

    st.markdown("#### Rules for this market")
    st.markdown(f"- **{rule['country']}**: {rule['rule']}. [Source]({rule['source_url']}) *(to verify)*")
    if rule["country"] != "EU":
        st.markdown("- **EU**: PPWR, all packaging recyclable by 2030. "
                    "[Source](https://eur-lex.europa.eu/eli/reg/2025/40/oj) *(to verify)*")


def main():
    st.set_page_config(page_title="Pack Swap Advisor", page_icon="♻️", layout="wide")
    st.title("♻️ Pack Swap Advisor")
    materials, products, rules, errors = load_data()
    if errors:
        for e in errors:
            st.error(e)
        st.stop()
    overview, analyse = st.tabs(["Overview", "Analyse a product"])
    with overview:
        overview_tab()
    with analyse:
        analyse_tab(materials, products, rules)


if __name__ == "__main__":
    main()
