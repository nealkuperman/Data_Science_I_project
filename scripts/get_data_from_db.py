#%%
import sys
from pathlib import Path
import pandas as pd

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine

_data_dir = _project_root / "data"

default_engine = get_engine()

def get_undrafted_players(engine = default_engine):
    query = """SELECT p.player_id, p.first_name, p.last_name, p.position, p.from_year
    FROM player p
    LEFT JOIN draft d ON p.player_id = d.player_id
    WHERE d.player_id IS NULL;"""
    result = pd.read_sql(query, engine)
    return(result)

def get_tables(engine = default_engine):
    tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
    tables = pd.read_sql(tables_query, engine)
    return tables 

def get_table_columns(table_name, engine = default_engine):
    cols_query = f"""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position;
    """
    return pd.read_sql(cols_query, engine)

def db_summary(engine = default_engine):
    # Database Summary
    print("=" * 50)
    print("DATABASE SUMMARY")
    print("=" * 50)

    # Get all tables
    tables = get_tables(engine)

    for table_name in tables['table_name']:
        # Get row count
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", engine)['count'][0]
        
        # Get columns
        columns = get_table_columns(table_name, engine)
        
        print(f"\n📋 {table_name.upper()} ({count} rows)")
        print("-" * 40)
        for _, row in columns.iterrows():
            print(f"   {row['column_name']}: {row['data_type']}")

    print("\n" + "=" * 50)

# %%

# db_summary()
# %%
