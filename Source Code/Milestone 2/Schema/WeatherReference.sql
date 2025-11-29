-- ========================================
-- 3. WeatherReference - How weather affects speed
-- ========================================
DROP TABLE IF EXISTS dbo.WeatherReference;
GO

CREATE TABLE dbo.WeatherReference (
    WeatherCondition  NVARCHAR(50) PRIMARY KEY,   -- Weather type
    SpeedImpactFactor FLOAT        NOT NULL      -- Speed multiplier
);
GO

INSERT INTO dbo.WeatherReference VALUES
('Clear',       1.000),
('Cloudy',      0.980),
('Light Rain',  0.920),
('Heavy Rain',  0.820),
('Foggy',       0.800),
('Sandstorm',   0.550);
GO