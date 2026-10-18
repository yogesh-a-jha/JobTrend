
import os
import re
import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

INPUT_FILE = os.path.join(
    "data", "processed", "job_listings_cleaned.csv"
)

OUTPUT_FILE = os.path.join(
    "data", "processed", "skill_demand.csv"
)

# Skills to identify in job titles, skills lists and descriptions.
# We can expand this dictionary as the project develops.
SKILL_PATTERNS = {
    "Python": r"\bpython\b",
    "Java": r"\bjava\b",
    "JavaScript": r"\bjavascript\b",
    "TypeScript": r"\btypescript\b",
    "C++": r"\bc\+\+\b",
    "SQL": r"\bsql\b",
    "React": r"\breact(?:\.js)?\b",
    "Node.js": r"\bnode(?:\.js|js)\b",
    "HTML": r"\bhtml5?\b",
    "CSS": r"\bcss3?\b",
    "Machine Learning": r"\bmachine learning\b",
    "Deep Learning": r"\bdeep learning\b",
    "Artificial Intelligence": r"\bartificial intelligence\b|\bai\b",
    "Data Analysis": r"\bdata analysis\b|\bdata analytics\b",
    "Data Science": r"\bdata science\b",
    "Excel": r"\bexcel\b",
    "Power BI": r"\bpower bi\b",
    "Tableau": r"\btableau\b",
    "AWS": r"\baws\b|\bamazon web services\b",
    "Azure": r"\bazure\b",
    "Google Cloud": r"\bgoogle cloud\b|\bgcp\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b",
    "Git": r"\bgit\b|\bgit hub\b|\bgithub\b",
    "Linux": r"\blinux\b",
    "Spark": r"\bspark\b|\bpyspark\b",
    "Hadoop": r"\bhadoop\b",
    "MongoDB": r"\bmongodb\b",
    "PostgreSQL": r"\bpostgresql\b|\bpostgres\b",
    "MySQL": r"\bmysql\b",
    "C#": r"\bc#\b",
    ".NET": r"\b\.net\b",
    "PHP": r"\bphp\b",
    "Flutter": r"\bflutter\b",
    "Android": r"\bandroid\b",
    "Figma": r"\bfigma\b",
    "Salesforce": r"\bsalesforce\b",
}


def main():
    spark = (
        SparkSession.builder
        .appName("JobTrend-Skill-Extraction")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(INPUT_FILE)
        )

        # Search the dedicated skill tags and the description.
        # Exclude the title initially to avoid counting skills
        # that only happen to occur in a job title.
        searchable_text = F.lower(
            F.concat_ws(
                " ",
                F.coalesce(F.col("tagsAndSkills"), F.lit("")),
                F.coalesce(F.col("jobDescription"), F.lit(""))
            )
        )

        # Count each skill at most once per job.
        skill_counts = []

        for skill, pattern in SKILL_PATTERNS.items():
            skill_counts.append(
                F.sum(
                    F.when(
                        searchable_text.rlike(pattern), 1
                    ).otherwise(0)
                ).alias(skill)
            )

        counts_row = df.select(*skill_counts).first()

        results = []
        total_jobs = df.count()

        for skill in SKILL_PATTERNS:
            count = counts_row[skill]
            count = int(count or 0)

            results.append(
                (skill, count, round(count / total_jobs * 100, 2))
            )

        result_df = spark.createDataFrame(
            results,
            ["skill", "job_count", "job_percentage"]
        )

        result_df = result_df.orderBy(
            F.desc("job_count"), F.asc("skill")
        )

        print("\n========== TOP 20 SKILLS ==========")
        result_df.show(20, truncate=False)

        # Write CSV via Pandas to avoid the Windows Hadoop
        # winutils.exe requirement encountered earlier.
        os.makedirs(
            os.path.dirname(OUTPUT_FILE),
            exist_ok=True
        )

        result_df.toPandas().to_csv(
            OUTPUT_FILE,
            index=False
        )

        print("Skill demand saved to:", OUTPUT_FILE)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
