# Iceberg Motion Features

This document describes the engineering of motion features from the cleaned NASA SCP iceberg trajectory dataset.

## Coordinate System
The raw dataset contains geographical coordinates (latitude and longitude) in WGS84 (EPSG:4326). 
To compute accurate distances and headings in the polar region, coordinates were projected into the **Antarctic Polar Stereographic** projection (**EPSG:3031**).
This yields cartesian coordinates `x_m` (Easting) and `y_m` (Northing) in metres.

## Calculated Features

### 1. Displacement and Distance
For an iceberg $i$ at time $t$:
- $\Delta x = x_m(t) - x_m(t-1)$
- $\Delta y = y_m(t) - y_m(t-1)$
- $distance = \sqrt{\Delta x^2 + \Delta y^2}$

### 2. Velocity
Velocity is calculated using the time gap since the previous observation:
- $velocity_{m/s} = \frac{distance}{\Delta t_{hours} \times 3600}$
- $velocity_{km/h} = velocity_{m/s} \times 3.6$

### 3. Heading
Heading is defined as the direction of movement, normalized to $[0, 360)$ degrees, where:
- 0° = North
- 90° = East
- 180° = South
- 270° = West

In EPSG:3031, the Y-axis points North along the Prime Meridian, and the X-axis points East along the 90°E meridian. 
The formula used is:
$heading = \text{arctan2}(\Delta x, \Delta y) \times \frac{180}{\pi}$

For zero-distance observations, heading is set to `NaN` as there is no direction of movement.

## Quality Flags
A categorical column `motion_quality_flag` was introduced to identify anomalies without deleting raw records:
1. `FIRST_OBSERVATION`: The first observation of an iceberg (no previous point to calculate motion from).
2. `INVALID_TIME`: The time interval is negative, zero, or missing.
3. `ANOMALOUS_VELOCITY`: The calculated velocity exceeds the physically realistic threshold.
4. `ZERO_MOVEMENT`: The displacement is exactly 0 metres.
5. `OK`: The record passes all checks.

### Anomalous Velocity Threshold
Icebergs are large masses strongly influenced by ocean currents and winds, but their sheer mass limits extreme velocities. 
A threshold of **3.0 m/s** (10.8 km/h) is used to flag anomalous observations. While small fragments or sea ice could theoretically travel this fast in a severe storm, tabular icebergs tracking at >3.0 m/s is typically indicative of a tracking misidentification or coordinate anomaly.
