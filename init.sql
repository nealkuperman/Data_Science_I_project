-- Run on first container init only (empty data volume).
-- Creates tables in nba_db, then in nba_db_test (schema/ is mounted at /schema).

\i /schema/01_tables.sql

\c nba_db_test
\i /schema/01_tables.sql
