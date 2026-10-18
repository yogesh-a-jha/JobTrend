import os
import sys

# Explicitly tell Spark which Python executable to use
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("JobTrend")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

print("Spark version:", spark.version)
print("Python executable:", sys.executable)

data = [
    ("Python", 120),
    ("Java", 95),
    ("JavaScript", 85),
]

df = spark.createDataFrame(
    data,
    ["skill", "job_count"]
)

df.show()

spark.stop()