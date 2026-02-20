-- NBA Database Schema
-- Creates all tables and indexes. Does not drop anything.
-- For a clean slate: run reset_tables.sql first, then this file.
--
-- Usage:
--   Production:  psql -U nba_user -d nba_db -f schema/01_tables.sql
--   Test:        psql -U nba_user -d nba_db_test -f schema/01_tables.sql

-- =============================================================================
-- TABLES (dependency order: team, player, draft, game, team_box_score, player_box_score)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- team
-- -----------------------------------------------------------------------------
CREATE TABLE team (
    team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(100),
    team_abbreviation VARCHAR(10),
    team_city VARCHAR(50),
    team_conference VARCHAR(10),
    team_division VARCHAR(20),
    team_code VARCHAR(50),
    team_slug VARCHAR(50)
);

-- -----------------------------------------------------------------------------
-- player
-- -----------------------------------------------------------------------------
CREATE TABLE player (
    player_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    position VARCHAR(20),
    height VARCHAR(10),
    weight VARCHAR(10),
    country VARCHAR(50),
    from_year INTEGER
);

-- -----------------------------------------------------------------------------
-- draft (references player, team)
-- -----------------------------------------------------------------------------
CREATE TABLE draft (
    draft_id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES player(player_id),
    draft_year INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    team_id INTEGER REFERENCES team(team_id),
    UNIQUE (player_id, draft_year)
);

-- -----------------------------------------------------------------------------
-- game (references team)
-- -----------------------------------------------------------------------------
CREATE TABLE game (
    game_id INTEGER PRIMARY KEY,
    game_date DATE,
    season_year VARCHAR(10),
    minutes_played INTEGER,
    home_team_id INTEGER REFERENCES team(team_id),
    away_team_id INTEGER REFERENCES team(team_id),
    home_score INTEGER CHECK (home_score >= 0),
    away_score INTEGER CHECK (away_score >= 0),
    overtime INTEGER CHECK (overtime >= 0),
    neutral_site INTEGER
);

-- -----------------------------------------------------------------------------
-- team_box_score (references game, team)
-- -----------------------------------------------------------------------------
CREATE TABLE team_box_score (
    team_box_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES game(game_id),
    team_id INTEGER REFERENCES team(team_id),
    is_home BOOLEAN,
    win BOOLEAN,
    pts INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct DECIMAL(5,3),
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct DECIMAL(5,3),
    ftm INTEGER,
    fta INTEGER,
    ft_pct DECIMAL(5,3),
    oreb INTEGER,
    dreb INTEGER,
    reb INTEGER,
    ast INTEGER,
    tov INTEGER,
    stl INTEGER,
    blk INTEGER,
    blka INTEGER,
    pf INTEGER,
    pfd INTEGER,
    UNIQUE (game_id, team_id),
    CHECK (
        pts >= 0 AND fgm >= 0 AND fga >= 0 AND
        fg3m >= 0 AND fg3a >= 0 AND ftm >= 0 AND
        fta >= 0 AND oreb >= 0 AND dreb >= 0 AND
        reb >= 0 AND ast >= 0 AND tov >= 0 AND
        stl >= 0 AND blk >= 0 AND blka >= 0 AND
        pf >= 0 AND pfd >= 0
    ),
    CHECK (fgm <= fga AND fg3m <= fg3a AND ftm <= fta)
);

-- -----------------------------------------------------------------------------
-- player_box_score (references game, player, team)
-- -----------------------------------------------------------------------------
CREATE TABLE player_box_score (
    player_box_id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES game(game_id),
    player_id INTEGER REFERENCES player(player_id),
    team_id INTEGER REFERENCES team(team_id),
    min_played DECIMAL(5,2),
    pts INTEGER,
    fgm INTEGER,
    fga INTEGER,
    fg_pct DECIMAL(5,3),
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct DECIMAL(5,3),
    ftm INTEGER,
    fta INTEGER,
    ft_pct DECIMAL(5,3),
    oreb INTEGER,
    dreb INTEGER,
    reb INTEGER,
    ast INTEGER,
    tov INTEGER,
    stl INTEGER,
    blk INTEGER,
    blka INTEGER,
    pf INTEGER,
    pfd INTEGER,
    plus_minus INTEGER,
    UNIQUE (game_id, player_id)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- game
CREATE INDEX idx_game_home_team_id ON game (home_team_id);
CREATE INDEX idx_game_away_team_id ON game (away_team_id);
CREATE INDEX idx_game_date ON game (game_date);
CREATE INDEX idx_game_season_year ON game (season_year);

-- team_box_score
CREATE INDEX idx_team_box_score_game_id ON team_box_score (game_id);
CREATE INDEX idx_team_box_score_team_id ON team_box_score (team_id);

-- player_box_score
CREATE INDEX idx_player_box_score_game_id ON player_box_score (game_id);
CREATE INDEX idx_player_box_score_player_id ON player_box_score (player_id);
CREATE INDEX idx_player_box_score_team_id ON player_box_score (team_id);
