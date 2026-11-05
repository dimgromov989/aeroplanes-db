-- Страны, за воздушным пространством которых ведется наблюдение.
-- south, north, west, east - границы страны (boundingbox из nominatim).
CREATE TABLE IF NOT EXISTS countries (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL UNIQUE,
    south DOUBLE PRECISION NOT NULL,
    north DOUBLE PRECISION NOT NULL,
    west  DOUBLE PRECISION NOT NULL,
    east  DOUBLE PRECISION NOT NULL
);

-- Воздушные суда, находящиеся в воздушном пространстве страны.
-- Границы стран прямоугольные и могут пересекаться, поэтому один самолет (icao24)
-- может встречаться в разных странах, но только один раз в каждой.
-- velocity - скорость, м/с; altitude - высота, м.
CREATE TABLE IF NOT EXISTS aeroplanes (
    id             SERIAL PRIMARY KEY,
    country_id     INTEGER NOT NULL REFERENCES countries (id) ON DELETE CASCADE,
    icao24         VARCHAR(10) NOT NULL,
    callsign       VARCHAR(16),
    origin_country VARCHAR(100) NOT NULL,
    velocity       DOUBLE PRECISION CHECK (velocity >= 0),
    altitude       DOUBLE PRECISION,
    on_ground      BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (country_id, icao24)
);

CREATE INDEX IF NOT EXISTS idx_aeroplanes_callsign ON aeroplanes (callsign);
