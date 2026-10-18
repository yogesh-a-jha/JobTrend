
import os
import sys
import pandas as pd

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. Start Spark
spark = (
    SparkSession.builder
    .appName("JobTrend-Dataset-Inspection")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# 2. Excel file path
file_path = os.path.join(
    "data",
    "raw",
    "indian-job-market-dataset-2025.xlsx"
)

try:
    # 3. Read Excel and inspect available sheets
    excel_file = pd.ExcelFile(file_path)

    print("\n========== EXCEL SHEETS ==========")
    print(excel_file.sheet_names)

    # Read the first sheet
    pandas_df = pd.read_excel(
        file_path,
        sheet_name=excel_file.sheet_names[0]
    )

    print("\n========== EXCEL COLUMN NAMES ==========")
    print(pandas_df.columns.tolist())

    # 4. Convert to Spark DataFrame
    df = spark.createDataFrame(pandas_df)

    print("\n========== SPARK SCHEMA ==========")
    df.printSchema()

    print("\n========== TOTAL ROWS ==========")
    print(df.count())

    print("\n========== FIRST 10 RECORDS ==========")
    df.show(10, truncate=False)

    # 5. Missing values
    print("\n========== MISSING VALUES ==========")

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

    # 6. Duplicate records
    total_rows = df.count()
    distinct_rows = df.dropDuplicates().count()

    print("\n========== DUPLICATE ROWS ==========")
    print("Total rows:", total_rows)
    print("Distinct rows:", distinct_rows)
    print("Duplicate rows:", total_rows - distinct_rows)

finally:
    spark.stop()
