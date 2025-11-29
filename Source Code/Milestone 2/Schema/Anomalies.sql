-- ========================================
-- 5. Anomalies - 5-minute summary of problems
-- ========================================
DROP TABLE IF EXISTS dbo.Anomalies;
GO

CREATE TABLE dbo.Anomalies (
    EventID       NVARCHAR(100) PRIMARY KEY,   -- e.g., EVT_LOC001_202511131030
    LocationID    NVARCHAR(10)  NOT NULL,
    LocationName  NVARCHAR(100) NOT NULL,
    Latitude      FLOAT         NOT NULL,
    Longitude     FLOAT         NOT NULL,
    AnomalyType   NVARCHAR(50)  NOT NULL,      -- Type of problem
    Severity      NVARCHAR(20)  NOT NULL,      -- critical, high, etc.
    Value         FLOAT         NULL,          -- Number that triggered alert
    Incident      NVARCHAR(50)  NULL,          -- What happened
    AvgSpeed      FLOAT         NOT NULL,
    MaxSpeed      FLOAT         NOT NULL,
    MinSpeed      FLOAT         NOT NULL,
    MaxCongestion FLOAT         NOT NULL,
    DetectedAt    DATETIME2     NOT NULL,      -- End of 5-minute window

    FOREIGN KEY (LocationID) REFERENCES dbo.Locations(LocationID),
    FOREIGN KEY (Incident)   REFERENCES dbo.IncidentReference(IncidentType)
);
GO

CREATE INDEX IX_Anomalies_DetectedAt ON dbo.Anomalies (DetectedAt DESC);
CREATE INDEX IX_Anomalies_Severity   ON dbo.Anomalies (Severity);
GO