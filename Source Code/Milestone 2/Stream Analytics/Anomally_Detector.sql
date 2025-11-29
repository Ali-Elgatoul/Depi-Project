WITH TrafficStats AS (
    SELECT
        System.Timestamp() AS AnalysisTime,
        LocationID,
        LocationName,
        Latitude,
        Longitude,
        AVG(AverageSpeedKMH) AS AvgSpeed,
        MAX(AverageSpeedKMH) AS MaxSpeed,
        MIN(AverageSpeedKMH) AS MinSpeed,
        MAX(CongestionPercentage) AS MaxCongestion,
        MAX(CAST(TrafficIncident AS NVARCHAR(MAX))) AS Incident
    FROM [TrafficInput]
    TIMESTAMP BY CAST([Timestamp] AS datetime)
    GROUP BY 
        LocationID, LocationName, Latitude, Longitude, 
        TumblingWindow(minute, 5)
),
AnomalyData AS (
    SELECT
        -- USE NVARCHAR(MAX) FOR STREAM ANALYTICS
        CAST(CONCAT('EVT_', LocationID, '_', 
               REPLACE(SUBSTRING(CAST(AnalysisTime AS NVARCHAR(MAX)), 12, 8), ':', '')) 
             AS NVARCHAR(MAX)) AS EventID,
        CAST(LocationID AS NVARCHAR(MAX)) AS LocationID,
        CAST(LocationName AS NVARCHAR(MAX)) AS LocationName,
        CAST(Latitude AS FLOAT) AS Latitude,
        CAST(Longitude AS FLOAT) AS Longitude,
        CAST(
            CASE
                WHEN Incident IN ('Major Accident', 'Road Closure') THEN 'critical_incident'
                WHEN AvgSpeed < 15 THEN 'severe_congestion'
                WHEN MaxCongestion > 100 THEN 'high_congestion'
                WHEN MaxSpeed > 90 THEN 'high_speed'
                WHEN (MaxSpeed - MinSpeed) > 30 THEN 'volatile_traffic'
                WHEN Incident <> 'None' THEN 'minor_incident'
                ELSE 'normal'
            END 
        AS NVARCHAR(MAX)) AS AnomalyType,
        CAST(
            CASE
                WHEN Incident IN ('Major Accident', 'Road Closure') THEN 'critical'
                WHEN AvgSpeed < 15 OR MaxCongestion > 100 THEN 'high'
                WHEN MaxSpeed > 90 OR (MaxSpeed - MinSpeed) > 30 THEN 'medium'
                WHEN Incident <> 'None' THEN 'low'
                ELSE 'normal'
            END 
        AS NVARCHAR(MAX)) AS Severity,
        CAST(
            CASE
                WHEN Incident IN ('Major Accident', 'Road Closure') THEN 100
                WHEN AvgSpeed < 15 THEN AvgSpeed
                WHEN MaxCongestion > 100 THEN MaxCongestion
                WHEN MaxSpeed > 90 THEN MaxSpeed
                WHEN (MaxSpeed - MinSpeed) > 30 THEN (MaxSpeed - MinSpeed)
                ELSE NULL
            END 
        AS FLOAT) AS Value,
        CAST(Incident AS NVARCHAR(MAX)) AS Incident,
        CAST(AvgSpeed AS FLOAT) AS AvgSpeed,
        CAST(MaxSpeed AS FLOAT) AS MaxSpeed,
        CAST(MinSpeed AS FLOAT) AS MinSpeed,
        CAST(MaxCongestion AS FLOAT) AS MaxCongestion,
        CAST(AnalysisTime AS DATETIME) AS DetectedAt
    FROM TrafficStats
)

SELECT
    EventID,
    LocationID,
    LocationName,
    Latitude,
    Longitude,
    AnomalyType,
    Severity,
    Value,
    Incident,
    AvgSpeed,
    MaxSpeed,
    MinSpeed,
    MaxCongestion,
    DetectedAt
INTO [AnomaliesOutput]
FROM AnomalyData
WHERE AnomalyType <> 'normal';