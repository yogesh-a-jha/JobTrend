
import os
import sys
import pandas as pd

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

INPUT_FILE = os.path.join(
    "data", "raw", "indian-job-market-dataset-2025.xlsx"
)

OUTPUT_FILE = os.path.join(
    "data", "processed", "job_listings_cleaned.csv"
)


def main():
    spark = (
        SparkSession.builder
        .appName("JobTrend-Data-Cleaning")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    try:
        # 1. Load Excel data
        pandas_df = pd.read_excel(INPUT_FILE)
        df = spark.createDataFrame(pandas_df)

        print("Original row count:", df.count())

        # 2. Remove exact duplicate records
        df = df.dropDuplicates()

        # 3. Clean text columns
        for column_name, data_type in df.dtypes:
            if data_type == "string":
                df = df.withColumn(
                    column_name,
                    F.when(
                        F.trim(F.col(column_name)) == "",
                        F.lit(None).cast("string")
                    ).otherwise(
                        F.trim(F.col(column_name))
                    )
                )

        # 4. Remove HTML tags from job descriptions
        if "jobDescription" in df.columns:
            df = df.withColumn(
                "jobDescription",
                F.regexp_replace(
                    F.col("jobDescription"),
                    r"<[^>]*>",
                    " "
                )
            )

            df = df.withColumn(
                "jobDescription",
                F.trim(
                    F.regexp_replace(
                        F.col("jobDescription"),
                        r"\s+",
                        " "
                    )
                )
            )

        # 5. Treat empty descriptions as missing
        if "jobDescription" in df.columns:
            df = df.withColumn(
                "jobDescription",
                F.when(
                    F.col("jobDescription") == "",
                    F.lit(None).cast("string")
                ).otherwise(F.col("jobDescription"))
            )

        # 6. Preserve missing values as unknown.
        # Do not fill missing ratings with zero.
        # Do not assume zero salary means a real salary.

        # 7. Display cleaning results
        print("\n========== CLEANING SUMMARY ==========")
        print("Rows after duplicate removal:", df.count())
        print("Columns:", len(df.columns))

        print("\n========== CLEANED SAMPLE ==========")
        df.show(5, truncate=80)

        print("\n========== REMAINING MISSING VALUES ==========")
        missing_exprs = [
            F.sum(
                F.when(
                    F.col(c).isNull()
                    | (F.trim(F.col(c).cast("string")) == ""),
                    1
                ).otherwise(0)
            ).alias(c)
            for c in df.columns
        ]
        df.select(*missing_exprs).show(
            truncate=False,
            vertical=True
        )

        # Save the Spark DataFrame through Pandas
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        cleaned_pdf = df.toPandas()
        cleaned_pdf.to_csv(OUTPUT_FILE, index=False)

        print("\nCleaned dataset saved to:", OUTPUT_FILE)
        print("Saved records:", len(cleaned_pdf))

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
