-- ========================================
-- 2. IncidentReference - How much each incident slows traffic
-- ========================================
DROP TABLE IF EXISTS dbo.IncidentReference;
GO

CREATE TABLE dbo.IncidentReference (
    IncidentType      NVARCHAR(50) PRIMARY KEY,   -- Name of incident
    SpeedImpactFactor FLOAT        NOT NULL      -- 1.0 = no effect, 0.45 = big slowdown
);
GO

INSERT INTO dbo.IncidentReference VALUES
('Major Accident',      0.450),
('Minor Accident',      0.750),
('None',                1.000),
('Police Checkpoint',   0.850),
('Road Construction',   0.550),
('Vehicle Breakdown',   0.650);
GO