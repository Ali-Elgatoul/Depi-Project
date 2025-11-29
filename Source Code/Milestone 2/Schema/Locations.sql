-- ========================================
-- 1. Locations - List of 7 Cairo spots
-- ========================================
DROP TABLE IF EXISTS dbo.Locations;
GO

CREATE TABLE dbo.Locations (
    LocationID   NVARCHAR(10)  PRIMARY KEY,   -- e.g., LOC001
    LocationName NVARCHAR(100) NOT NULL,      -- Name of the place
    Latitude     FLOAT         NOT NULL,      -- GPS latitude
    Longitude    FLOAT         NOT NULL,      -- GPS longitude
    MaxCapacity  INT           NOT NULL       -- Max vehicles it can hold
);
GO

INSERT INTO dbo.Locations VALUES
('LOC001', 'Tahrir Square',            30.0444, 31.2357, 120),
('LOC002', 'Ramses Square',            30.0626, 31.2497, 150),
('LOC003', '6th October Bridge',       30.0626, 31.2444, 100),
('LOC004', 'Nasr City - Abbas El Akkad', 30.0515, 31.3381, 80),
('LOC005', 'Heliopolis - Uruba Street', 30.0808, 31.3239, 90),
('LOC006', 'Maadi Corniche',           29.9594, 31.2584, 60),
('LOC007', 'Ahmed Orabi Square',       30.0618, 31.2001, 110);
GO