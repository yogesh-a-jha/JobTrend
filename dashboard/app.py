from pathlib import Path
import re
import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# JobTrend | Advanced Indian Job Market Analytics
# ============================================================
st.set_page_config(
    page_title="JobTrend | Job Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

# ---------- UI styling ----------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px;}
      [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(56, 139, 253, .12), rgba(56, 139, 253, .025));
        border: 1px solid rgba(128, 128, 128, .22);
        padding: 17px 18px; border-radius: 15px;
      }
      [data-testid="stMetricLabel"] {font-size: .9rem;}
      [data-testid="stMetricValue"] {font-size: 1.75rem;}
      .hero {
        padding: 1.25rem 1.5rem; border-radius: 18px;
        background: linear-gradient(120deg, rgba(50,115,220,.22), rgba(32,201,151,.09));
        border: 1px solid rgba(128,128,128,.22); margin-bottom: 1rem;
      }
      .muted {opacity: .72; font-size: .9rem;}
      div[data-testid="stTabs"] button {font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
def norm_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def find_col(frame, candidates):
    mapping = {norm_name(c): c for c in frame.columns}
    for candidate in candidates:
        if norm_name(candidate) in mapping:
            return mapping[norm_name(candidate)]
    return None


def numeric(series):
    # Handles values such as "₹ 500,000", "500000", and blank strings.
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("INR", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def read_processed(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(path, low_memory=False)
        frame.columns = [str(c).replace("\ufeff", "").strip() for c in frame.columns]
        return frame
    except Exception as exc:
        st.warning(f"Could not read `{filename}`: {exc}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Loading the job-market dataset...")
def load_jobs():
    path = DATA_DIR / "job_listings_cleaned.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path, low_memory=False)
    frame.columns = [str(c).replace("\ufeff", "").strip() for c in frame.columns]
    return frame


def count_col(frame):
    return find_col(
        frame,
        ["jobCount", "job_count", "count", "jobs", "totalJobs",
         "total_jobs", "numberOfJobs", "listings", "count(1)"],
    )


def chart_layout(fig, height=430):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=65, b=10),
        legend_title_text="",
        hoverlabel=dict(namelength=-1),
    )
    return fig


def section_intro(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def top_bar(frame, label_col, value_col, title, top_n=15, horizontal=True):
    plot = frame[[label_col, value_col]].copy()
    plot[value_col] = numeric(plot[value_col])
    plot = plot.dropna(subset=[label_col, value_col])
    plot[label_col] = plot[label_col].astype(str)
    plot = plot.nlargest(top_n, value_col)
    if plot.empty:
        st.info("There is not enough valid data to draw this chart.")
        return
    if horizontal:
        plot = plot.sort_values(value_col)
        fig = px.bar(
            plot, x=value_col, y=label_col, orientation="h", text=value_col,
            title=title, labels={value_col: "Job listings", label_col: ""},
        )
    else:
        fig = px.bar(
            plot, x=label_col, y=value_col, text=value_col, title=title,
            labels={value_col: "Job listings", label_col: ""},
        )
        fig.update_xaxes(tickangle=-30)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    st.plotly_chart(chart_layout(fig, max(360, min(650, 28 * len(plot) + 120))), use_container_width=True)


# ---------- Load data ----------
jobs = load_jobs()
skills = read_processed("skill_demand.csv")
locations_agg = read_processed("top_locations.csv")
titles_agg = read_processed("top_job_titles.csv")
experience_agg = read_processed("experience_distribution.csv")
salary_agg = read_processed("salary_by_title.csv")

if jobs.empty:
    st.title("📊 JobTrend")
    st.error(
        "Could not load the cleaned dataset. Expected file:\n\n"
        f"`{DATA_DIR / 'job_listings_cleaned.csv'}`\n\n"
        "Run the data-cleaning script first, then refresh this page."
    )
    st.stop()

# Detect relevant columns
title_col = find_col(jobs, ["title", "jobTitle", "job_title", "role"])
location_col = find_col(jobs, ["location", "city"])
company_col = find_col(jobs, ["companyName", "company_name", "company"])
min_salary_col = find_col(jobs, ["minimumSalary", "minimum_salary", "minSalary"])
max_salary_col = find_col(jobs, ["maximumSalary", "maximum_salary", "maxSalary"])
currency_col = find_col(jobs, ["currency"])
min_exp_col = find_col(jobs, ["minimumExperience", "minimum_experience", "minExperience"])
max_exp_col = find_col(jobs, ["maximumExperience", "maximum_experience", "maxExperience"])
uploaded_col = find_col(jobs, ["jobUploaded", "datePosted", "postedDate", "date"])

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
      <h1 style="margin:0">📊 JobTrend</h1>
      <p style="margin:.35rem 0 0 0">Indian Job Market Intelligence · 2025 dataset</p>
      <p class="muted" style="margin:.35rem 0 0 0">
        Explore hiring patterns, in-demand skills, experience requirements and salary signals.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar filters ----------
st.sidebar.title("🎛️ Explore the market")
st.sidebar.caption("Filters apply to listing-level metrics and analyses where applicable.")

filtered = jobs.copy()

if location_col:
    loc_counts = filtered[location_col].dropna().astype(str).value_counts()
    loc_options = loc_counts.head(150).index.tolist()
    selected_locations = st.sidebar.multiselect(
        "Location (top 150)", loc_options, help="Leave blank to include all locations."
    )
    if selected_locations:
        filtered = filtered[filtered[location_col].astype(str).isin(selected_locations)]

if title_col:
    title_counts = filtered[title_col].dropna().astype(str).value_counts()
    title_options = title_counts.head(200).index.tolist()
    selected_titles = st.sidebar.multiselect(
        "Job title (top 200)", title_options, help="Leave blank to include all job titles."
    )
    if selected_titles:
        filtered = filtered[filtered[title_col].astype(str).isin(selected_titles)]

if company_col:
    company_options = (
        filtered[company_col].dropna().astype(str).value_counts().head(100).index.tolist()
    )
    selected_companies = st.sidebar.multiselect("Company (top 100)", company_options)
    if selected_companies:
        filtered = filtered[filtered[company_col].astype(str).isin(selected_companies)]

if st.sidebar.button("↻ Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Source: `{DATA_DIR.name}` processed CSV files")
st.sidebar.caption("Salary values are shown in source units; currencies are not converted.")

# ---------- KPI cards ----------
section_intro("Market overview", "Key indicators for the current filter selection.")
salary_values = numeric(filtered[min_salary_col]) if min_salary_col else pd.Series(dtype=float)
salary_values = salary_values[salary_values > 0].dropna()
median_salary = salary_values.median() if not salary_values.empty else None

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Job listings", f"{len(filtered):,}")
k2.metric("Companies", f"{filtered[company_col].nunique():,}" if company_col else "N/A")
k3.metric("Locations", f"{filtered[location_col].nunique():,}" if location_col else "N/A")
k4.metric("Median min. salary", f"{median_salary:,.0f}" if median_salary is not None else "N/A")
k5.metric("Titles", f"{filtered[title_col].nunique():,}" if title_col else "N/A")

if currency_col:
    currencies = filtered[currency_col].dropna().astype(str).value_counts()
    if len(currencies) > 1:
        st.warning(
            "The filtered listings contain multiple currencies. Salary values are not "
            "currency-normalized, so do not compare them directly across currencies."
        )

st.markdown("---")

# ---------- Main analysis tabs ----------
tab_overview, tab_skills, tab_salary, tab_experience, tab_data = st.tabs(
    ["📈 Market overview", "🔥 Skills intelligence", "💰 Salary explorer", "🎓 Experience", "🧾 Data explorer"]
)

with tab_overview:
    c1, c2 = st.columns(2)
    with c1:
        section_intro("Top locations", "Most frequent location groups in the processed aggregate.")
        loc_label = find_col(locations_agg, ["location_group", "locationGroup", "location", "city"])
        loc_count = count_col(locations_agg)
        if not locations_agg.empty and loc_label and loc_count:
            top_bar(locations_agg, loc_label, loc_count, "Top job locations", 15)
        elif location_col:
            loc_frame = filtered[location_col].dropna().astype(str).value_counts().head(15).rename_axis("Location").reset_index(name="Jobs")
            top_bar(loc_frame, "Location", "Jobs", "Top locations in current selection", 15)
        else:
            st.info("Location data is unavailable.")
    with c2:
        section_intro("Most common job titles", "Roles with the largest number of listings.")
        role_label = find_col(titles_agg, ["title", "jobTitle", "job_title", "role", "jobRole"])
        role_count = count_col(titles_agg)
        if not titles_agg.empty and role_label and role_count:
            top_bar(titles_agg, role_label, role_count, "Top job titles", 15)
        elif title_col:
            role_frame = filtered[title_col].dropna().astype(str).value_counts().head(15).rename_axis("Role").reset_index(name="Jobs")
            top_bar(role_frame, "Role", "Jobs", "Top roles in current selection", 15)
        else:
            st.info("Job-title data is unavailable.")

    st.markdown("---")
    section_intro("Quick insights", "Automatically generated from the currently selected job listings.")
    insight_cols = st.columns(3)
    with insight_cols[0]:
        if location_col:
            popular_loc = filtered[location_col].dropna().astype(str).value_counts()
            if not popular_loc.empty:
                st.metric("Most listed location", popular_loc.index[0], f"{popular_loc.iloc[0]:,} listings")
            else:
                st.metric("Most listed location", "N/A")
        else:
            st.metric("Most listed location", "N/A")
    with insight_cols[1]:
        if title_col:
            popular_role = filtered[title_col].dropna().astype(str).value_counts()
            if not popular_role.empty:
                st.metric("Most common role", popular_role.index[0], f"{popular_role.iloc[0]:,} listings")
            else:
                st.metric("Most common role", "N/A")
        else:
            st.metric("Most common role", "N/A")
    with insight_cols[2]:
        if company_col:
            top_company = filtered[company_col].dropna().astype(str).value_counts()
            if not top_company.empty:
                st.metric("Most active company", top_company.index[0], f"{top_company.iloc[0]:,} listings")
            else:
                st.metric("Most active company", "N/A")
        else:
            st.metric("Most active company", "N/A")

    if uploaded_col:
        dates = pd.to_datetime(filtered[uploaded_col], errors="coerce", dayfirst=True)
        date_frame = pd.DataFrame({"date": dates}).dropna()
        if not date_frame.empty and date_frame["date"].nunique() > 1:
            date_frame["month"] = date_frame["date"].dt.to_period("M").astype(str)
            monthly = date_frame.groupby("month").size().reset_index(name="Listings")
            fig = px.line(monthly, x="month", y="Listings", markers=True, title="Job postings over time")
            st.plotly_chart(chart_layout(fig, 380), use_container_width=True)
        else:
            st.caption("Posting-date trend is not shown because there are not enough parseable dates.")

with tab_skills:
    section_intro("In-demand skills", "Counts come from the project's dictionary-based skill extraction.")
    skill_label = find_col(skills, ["skill", "skillName", "skill_name", "technology", "technologyName"])
    skill_count = count_col(skills)
    if not skills.empty and skill_label and skill_count:
        skill_frame = skills.copy()
        skill_frame[skill_count] = numeric(skill_frame[skill_count])
        skill_frame = skill_frame.dropna(subset=[skill_count]).sort_values(skill_count, ascending=False)
        if not skill_frame.empty:
            total_jobs = len(jobs)
            skill_frame["Share of all listings (%)"] = (
                skill_frame[skill_count] / total_jobs * 100 if total_jobs else 0
            )
            left, right = st.columns([1.4, 1])
            with left:
                top_bar(skill_frame, skill_label, skill_count, "Top skills by listing count", 20)
            with right:
                st.markdown("#### Skill demand table")
                display = skill_frame.head(20).copy()
                display = display.rename(columns={skill_label: "Skill", skill_count: "Job listings"})
                if "Share of all listings (%)" in display:
                    display["Share of all listings (%)"] = display["Share of all listings (%)"].round(2)
                st.dataframe(display, use_container_width=True, hide_index=True, height=500)
            st.info(
                "Interpretation: these are keyword mentions in job descriptions/tags, not a "
                "guarantee that every listing requires the skill. The dictionary approach can "
                "miss synonyms and may occasionally match ambiguous terms."
            )
        else:
            st.warning("The skill aggregate has no valid counts.")
    else:
        st.warning(
            "Could not identify skill and count columns in skill_demand.csv. "
            f"Found columns: {list(skills.columns)}"
        )

    # If original tags exist, allow transparent skill keyword search in current filtered records.
    tags_col = find_col(filtered, ["tagsAndSkills", "tags_and_skills", "skills"])
    desc_col = find_col(filtered, ["jobDescription", "job_description", "description"])
    if tags_col or desc_col:
        st.markdown("---")
        st.markdown("#### Search listings for a skill or keyword")
        query = st.text_input("Keyword", placeholder="e.g. Python, SQL, React")
        if query.strip():
            text_fields = [c for c in [tags_col, desc_col] if c]
            mask = pd.Series(False, index=filtered.index)
            for col in text_fields:
                mask |= filtered[col].fillna("").astype(str).str.contains(
                    re.escape(query.strip()), case=False, regex=True
                )
            matches = filtered.loc[mask]
            st.metric("Matching listings", f"{len(matches):,}")
            st.dataframe(matches.head(100), use_container_width=True, hide_index=True)

with tab_salary:
    section_intro("Salary explorer", "Explore the advertised minimum and maximum salaries available in the dataset.")
    if min_salary_col:
        salary_frame = filtered.copy()
        salary_frame["_min_salary"] = numeric(salary_frame[min_salary_col])
        salary_frame["_max_salary"] = numeric(salary_frame[max_salary_col]) if max_salary_col else pd.NA
        salary_frame = salary_frame[salary_frame["_min_salary"] > 0]
        if currency_col:
            currency_values = salary_frame[currency_col].dropna().astype(str).unique()
            if len(currency_values) > 1:
                chosen_currency = st.selectbox("Currency", ["All currencies"] + sorted(currency_values.tolist()))
                if chosen_currency != "All currencies":
                    salary_frame = salary_frame[salary_frame[currency_col].astype(str) == chosen_currency]

        if not salary_frame.empty:
            a, b, c = st.columns(3)
            a.metric("Listings with minimum salary", f"{len(salary_frame):,}")
            b.metric("Median minimum", f"{salary_frame['_min_salary'].median():,.0f}")
            valid_max = salary_frame["_max_salary"].dropna()
            c.metric("Median maximum", f"{valid_max[valid_max > 0].median():,.0f}" if not valid_max.empty and (valid_max > 0).any() else "N/A")

            salary_plot = salary_frame[salary_frame["_min_salary"] > 0].copy()
            # Trim extreme tails only for the visualization; retain all data in source/table.
            upper = salary_plot["_min_salary"].quantile(0.99)
            plot_data = salary_plot[salary_plot["_min_salary"] <= upper]
            fig = px.histogram(
                plot_data, x="_min_salary", nbins=40, marginal="box",
                title="Distribution of minimum advertised salary (up to 99th percentile)",
                labels={"_min_salary": "Minimum salary (source units)", "count": "Listings"},
            )
            st.plotly_chart(chart_layout(fig, 430), use_container_width=True)
            st.caption("The histogram excludes the top 1% of minimum-salary values for readability; the metrics above use the full filtered salary data.")

            if title_col:
                by_role = salary_frame.dropna(subset=[title_col]).groupby(title_col).agg(
                    Listings=("_min_salary", "size"),
                    MedianMinimum=("_min_salary", "median"),
                    MeanMinimum=("_min_salary", "mean"),
                ).reset_index()
                by_role = by_role[by_role["Listings"] >= 5].nlargest(20, "MedianMinimum")
                if not by_role.empty:
                    fig = px.bar(
                        by_role.sort_values("MedianMinimum"),
                        x="MedianMinimum", y=title_col, orientation="h",
                        color="Listings", hover_data=["MeanMinimum", "Listings"],
                        title="Roles with highest median minimum salary (at least 5 listings)",
                        labels={"MedianMinimum": "Median minimum salary", title_col: "Job title"},
                    )
                    st.plotly_chart(chart_layout(fig, 600), use_container_width=True)
                else:
                    st.info("Not enough role groups with five or more valid salary listings.")
        else:
            st.info("No valid positive salary values are available under the current filters.")
    else:
        st.warning("The cleaned dataset has no recognizable minimum salary column.")

    if not salary_agg.empty:
        with st.expander("View precomputed salary aggregates"):
            st.dataframe(salary_agg, use_container_width=True, hide_index=True)

with tab_experience:
    section_intro("Experience requirements", "Understand the experience bands requested by employers.")
    if min_exp_col:
        exp_frame = filtered.copy()
        exp_frame["_min_exp"] = numeric(exp_frame[min_exp_col])
        exp_frame = exp_frame.dropna(subset=["_min_exp"])
        exp_frame = exp_frame[exp_frame["_min_exp"] >= 0]
        if not exp_frame.empty:
            exp_frame["Experience band"] = pd.cut(
                exp_frame["_min_exp"],
                bins=[-0.1, 0, 2, 5, 10, float("inf")],
                labels=["Fresher / 0 years", "1–2 years", "3–5 years", "6–10 years", "10+ years"],
                include_lowest=True,
            )
            exp_counts = exp_frame["Experience band"].value_counts(sort=False).reset_index()
            exp_counts.columns = ["Experience band", "Listings"]
            c1, c2 = st.columns([1, 1])
            with c1:
                fig = px.pie(
                    exp_counts, names="Experience band", values="Listings", hole=.48,
                    title="Experience mix", hover_data=["Listings"],
                )
                st.plotly_chart(chart_layout(fig, 420), use_container_width=True)
            with c2:
                fig = px.bar(
                    exp_counts, x="Experience band", y="Listings", text="Listings",
                    title="Listings by experience band",
                )
                fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                st.plotly_chart(chart_layout(fig, 420), use_container_width=True)
            st.dataframe(exp_counts, use_container_width=True, hide_index=True)
        else:
            st.info("No valid non-negative minimum-experience values are available.")
    elif not experience_agg.empty:
        st.dataframe(experience_agg, use_container_width=True, hide_index=True)
        st.caption("Showing the precomputed experience aggregate because a raw experience column was not detected.")
    else:
        st.warning("No recognizable experience column or precomputed aggregate was found.")

with tab_data:
    section_intro("Data explorer", "Inspect the records behind the dashboard and export the filtered selection.")
    st.write(f"**{len(filtered):,}** records match your current filters.")
    preview_cols = [c for c in [
        title_col, location_col, company_col, min_salary_col, max_salary_col,
        min_exp_col, max_exp_col, currency_col, uploaded_col
    ] if c and c in filtered.columns]
    preview_cols = list(dict.fromkeys(preview_cols))
    if not preview_cols:
        preview_cols = filtered.columns[:12].tolist()
    st.dataframe(filtered[preview_cols].head(250), use_container_width=True, hide_index=True)
    export_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered listings as CSV",
        data=export_data,
        file_name="jobtrend_filtered_listings.csv",
        mime="text/csv",
    )

    with st.expander("Data quality snapshot"):
        quality = pd.DataFrame({
            "Column": filtered.columns,
            "Missing values": [int(filtered[c].isna().sum()) for c in filtered.columns],
            "Missing (%)": [
                round(float(filtered[c].isna().mean() * 100), 2) for c in filtered.columns
            ],
        }).sort_values("Missing (%)", ascending=False)
        st.dataframe(quality, use_container_width=True, hide_index=True)

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "JobTrend · Big Data Analysis Mini Project · PySpark + Pandas + Streamlit + Plotly. "
    "Insights are descriptive and reflect the source dataset; they do not establish causation."
)
