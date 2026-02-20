import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import adapt
from psycopg2.extras import execute_values

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_TEST_URL = os.getenv("DATABASE_TEST_URL")

