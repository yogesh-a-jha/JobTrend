
import os
import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

INPUT_FILE = os.path.join(
    "data", "processed", "job_listings_cleaned.csv"
)

OUTPUT_DIR = os.path.join("data", "processed")


def save_result(df, filename):
    """Save a small aggregated Spark DataFrame as CSV."""
    output_path = os.path.join(OUTPUT_DIR, filename)
    df.toPandas().to_csv(output_path, index=False)
    print(f"Saved: {output_path}")


def main():
    spark = (
        SparkSession.builder
        .appName("JobTrend-Analytics")
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

        
        # Convert numeric columns explicitly.
        # Invalid values become NULL instead of crashing Spark.
        for column_name in [
            "minimumExperience",
            "maximumExperience",
            "minimumSalary",
            "maximumSalary",
        ]:
            df = df.withColumn(
                column_name,
                F.expr(f"try_cast(`{column_name}` AS DOUBLE)")
            )


        total_jobs = df.count()

        print("\n========== DATASET OVERVIEW ==========")
        print("Total job listings:", total_jobs)
        print("Total columns:", len(df.columns))

        # 1. Top locations
        locations = (
            df.withColumn(
                "location_group",
                F.trim(
                    F.split(F.col("location"), ",").getItem(0)
                )
            )
            .filter(
                F.col("location_group").isNotNull()
                & (F.col("location_group") != "")
            )
            .groupBy("location_group")
            .agg(F.count("*").alias("job_count"))
            .orderBy(F.desc("job_count"))
            .limit(20)
        )

        print("\n========== TOP 20 LOCATIONS ==========")
        locations.show(truncate=False)
        save_result(locations, "top_locations.csv")

        # 2. Most common job titles
        job_titles = (
            df.groupBy("title")
            .agg(F.count("*").alias("job_count"))
            .orderBy(F.desc("job_count"))
            .limit(20)
        )

        print("\n========== TOP 20 JOB TITLES ==========")
        job_titles.show(truncate=False)
        save_result(job_titles, "top_job_titles.csv")

        # 3. Experience distribution
        # Use minimumExperience where available.
        # Missing experience remains explicitly unknown.
        experience_df = df.withColumn(
            "experience_band",
            F.when(
                F.col("minimumExperience").isNull(),
                "Unknown"
            )
            .when(
                F.col("minimumExperience") < 0,
                "Unknown"
            )
            .when(
                F.col("minimumExperience") == 0,
                "Fresher / 0 years"
            )
            .when(
                F.col("minimumExperience") <= 2,
                "1-2 years"
            )
            .when(
                F.col("minimumExperience") <= 5,
                "3-5 years"
            )
            .when(
                F.col("minimumExperience") <= 10,
                "6-10 years"
            )
            .otherwise("10+ years")
        )

        experience_distribution = (
            experience_df
            .groupBy("experience_band")
            .agg(F.count("*").alias("job_count"))
            .orderBy(F.desc("job_count"))
        )

        print("\n========== EXPERIENCE DISTRIBUTION ==========")
        experience_distribution.show(truncate=False)
        save_result(
            experience_distribution,
            "experience_distribution.csv"
        )

        # 4. Salary trends by job title.
        # Zero salary values represent unavailable/
        # undisclosed salary data in this dataset.
        valid_salary_df = df.filter(
            (F.col("minimumSalary") > 0)
            & (F.col("maximumSalary") >= F.col("minimumSalary"))
        )

        salary_by_title = (
            valid_salary_df
            .groupBy("title")
            .agg(
                F.count("*").alias("job_count"),
                F.round(
                    F.avg("minimumSalary"), 0
                ).alias("avg_minimum_salary"),
                F.round(
                    F.avg("maximumSalary"), 0
                ).alias("avg_maximum_salary")
            )
            .filter(F.col("job_count") >= 5)
            .orderBy(
                F.desc("job_count"),
                F.asc("title")
            )
            .limit(20)
        )

        print("\n========== SALARY TRENDS BY JOB TITLE ==========")
        salary_by_title.show(truncate=False)
        save_result(salary_by_title, "salary_by_title.csv")

        print("\n========== ANALYTICS COMPLETED ==========")
        print("Processed job listings:", total_jobs)
        print("Results directory:", OUTPUT_DIR)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
