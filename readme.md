# JobTrend --- Big Data Analytics for Indian Job Market Trends

JobTrend is a data analytics project that explores job listings in the
Indian job market. It uses **PySpark** to process and analyze a large
job-listings dataset, Python-based skill extraction to identify
in-demand technologies, and **Streamlit** to present the results in an
interactive dashboard.

> **Dataset note:** The current version analyzes a static 2025 dataset.
> It does not fetch live job postings automatically. Salary values are
> displayed in the source dataset's units and are not
> currency-converted.

## Features

-   **Data cleaning:** removes duplicate listings and prepares the
    dataset for analysis.
-   **Skill-demand analysis:** searches job skills and descriptions for
    technology keywords and counts their occurrence across listings.
-   **Location analysis:** identifies locations with the most listings.
-   **Job-title analysis:** explores frequently listed job roles.
-   **Salary exploration:** summarizes salary fields by job title where
    data is available.
-   **Experience analysis:** examines experience requirements across
    listings.
-   **Interactive dashboard:** filters results and presents charts,
    KPIs, and job-listing data.
-   **Data export:** allows filtered listings to be downloaded from the
    dashboard.
-   **Data-quality overview:** highlights missing values in important
    columns.

## Tech Stack

-   **Language:** Python
-   **Big data processing:** Apache Spark / PySpark
-   **Dashboard:** Streamlit
-   **Data manipulation:** Pandas
-   **Visualizations:** Plotly
-   **Dataset format:** Excel and CSV
-   **Development environment:** VS Code

## Project Structure

``` text
JobTrend/
├── data/
│   ├── raw/
│   │   └── indian-job-market-dataset-2025.xlsx
│   └── processed/
│       ├── job_listings_cleaned.csv
│       ├── skill_demand.csv
│       ├── top_locations.csv
│       ├── top_job_titles.csv
│       ├── experience_distribution.csv
│       └── salary_by_title.csv
├── src/
│   ├── data_cleaning.py
│   ├── skill_extraction.py
│   └── analytics.py
├── dashboard/
│   └── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The dashboard expects the processed CSV files to be available under
`data/processed/`. Keep the folder and filenames consistent with the
paths used in the code.

## Dataset

The source file is `indian-job-market-dataset-2025.xlsx`.

-   **Rows in the original dataset:** 97,929
-   **Distinct rows after duplicate removal:** 97,682
-   **Columns:** 17
-   **Example fields:** job title, company, location, skills,
    experience, salary range, posting date, job description, reviews,
    and company rating.

The dataset contains missing values, particularly in company reviews and
ratings, so not every listing can be used for every analysis.

## Getting Started

### 1. Clone the repository

``` bash
git clone https://github.com/YOUR_USERNAME/JobTrend.git
cd JobTrend
```

Replace `YOUR_USERNAME` with your GitHub username and use your actual
repository URL.

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, follow your system's Python/PowerShell
environment guidance or activate the environment using your preferred
terminal.

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For dashboard-only deployment, the app uses Streamlit, Pandas, and
Plotly. The data-processing scripts also require PySpark and a
compatible Java installation. Make sure `requirements.txt` includes the
dependencies needed for the tasks you intend to run.

### 4. Run the dashboard

From the repository root:

``` powershell
streamlit run dashboard/app.py
```

Streamlit will print a local URL, commonly `http://localhost:8501`, in
the terminal.

## Run the Data Pipeline

Run the scripts from the repository root, in this order:

``` powershell
python src/data_cleaning.py
python src/skill_extraction.py
python src/analytics.py
```

The cleaning script prepares the source data, the skill-extraction
script generates skill-demand counts, and the analytics script creates
aggregate CSV files for the dashboard.

> Run the pipeline only after placing the source Excel dataset at the
> expected path. The scripts may overwrite processed output files.

## Key Findings from the Current Dataset

The current keyword-based skill extraction produced the following most
frequently detected skills:

    Rank Skill                       Listings detected
  ------ ------------------------- -------------------
       1 Python                                  7,530
       2 SQL                                     7,127
       3 Java                                    5,747
       4 CSS                                     4,930
       5 Azure                                   4,508
       6 Excel                                   4,464
       7 AWS                                     4,403
       8 JavaScript                              3,839
       9 Git                                     3,377
      10 Artificial Intelligence                 3,200

These counts are generated by keyword matching against the skills and
job-description text. They indicate detected mentions in this dataset,
not a complete measure of the entire Indian job market. Keyword matching
may miss synonyms and can sometimes produce false positives.

## Deploy to Streamlit Community Cloud

1.  Push the project to a GitHub repository.
2.  Confirm that `dashboard/app.py`, `requirements.txt`, and all
    required processed CSV files are committed.
3.  Open [Streamlit Community Cloud](https://share.streamlit.io/).
4.  Create a new app and connect the GitHub repository.
5.  Set the main file path to `dashboard/app.py`.
6.  Deploy the app and check the deployment logs if it fails.

**Important:** Do not commit your virtual environment, secrets, or
credentials. GitHub has file-size limits, so check the size of the
source dataset before pushing it. If the dataset is too large or cannot
be redistributed, document how to obtain it and keep it out of the
repository.

## Limitations and Future Improvements

-   **Static dataset:** the current project does not automatically
    retrieve new job listings.
-   **Keyword-based skill extraction:** a dictionary approach can miss
    alternate spellings and context, or match a keyword when it is not
    being used as a skill.
-   **Salary comparability:** source currencies and salary conventions
    may differ; values should not be compared across currencies without
    normalization.
-   **Missing data:** some listings lack salary, experience, or
    company-review information.
-   **Representativeness:** findings describe the supplied dataset and
    should not be treated as a complete census of the Indian job market.

Potential next steps:

-   Add a compliant, documented data-refresh workflow using an
    authorized source.
-   Normalize currencies and salary periods before making comparisons.
-   Improve skill extraction with alias dictionaries, phrase boundaries,
    and NLP methods.
-   Add time-based trend analysis when posting dates are reliable.
-   Add automated data-quality checks and pipeline tests.
-   Document data provenance, licensing, and update frequency.

## Author

**Yogesh Jha**\
Computer Engineering

## License and Data Usage

Add a project license before redistributing this code. Confirm the
dataset's source, license, and redistribution terms before publishing
the raw dataset or deploying it publicly. This README does not grant
rights to the dataset.
