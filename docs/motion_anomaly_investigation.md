# Motion Anomaly Investigation

## 1. Anomalous Velocity Records
Two records were flagged by the `ANOMALOUS_VELOCITY` flag (velocity > 3.0 m/s).

### Record 1: Iceberg `a68l`
* **Timestamp:** 2021-02-01 (Previous: 2020-12-31)
* **Coordinates:** `(-57.33, -35.81)` (Previous: `0.0, 0.0`)
* **Distance Jump:** 9,650,501 m (~9,650 km)
* **Time Gap:** 768.0 hours (32 days)
* **Velocity:** 3.49 m/s (12.56 km/h)
* **Cause:** **Coordinate Error / Missing Data Encoding**. The previous observation was recorded as exactly `0.0, 0.0` (equator), causing a massive, artificial jump to the actual location in Antarctica.

### Record 2: Iceberg `a74a` (Also the Maximum Velocity Record)
* **Timestamp:** 2026-03-18 (Previous: 2026-03-12)
* **Coordinates:** `(-57.88, -18.96)` (Previous: `(-61.25, -54.15)`)
* **Distance Jump:** 2,079,488 m (~2,079 km)
* **Time Gap:** 144.0 hours (6 days)
* **Velocity:** 4.01 m/s (14.44 km/h)
* **Cause:** **Tracking Error / Misidentification**. A 2,000 km movement in 6 days is physically impossible for an iceberg. The longitude jumped from -54° to -18°. This indicates either a typo in the original dataset's telemetry or the tracker locking onto a different target.

## 2. Maximum Distance Record
* **Iceberg ID:** `a76`
* **Timestamp:** 2021-05-19 (Previous: 2020-12-31)
* **Coordinates:** `(-75.15, -59.05)` (Previous: `0.0, 0.0`)
* **Distance Jump:** 11,616,716 m (~11,616 km)
* **Time Gap:** 3,336.0 hours (139 days)
* **Velocity:** 0.96 m/s
* **Cause:** **Coordinate Error**. Like `a68l`, the previous coordinate was recorded as `0.0, 0.0`. Because the time gap was very large (139 days), the resulting velocity (0.96 m/s) did not exceed the 3.0 m/s anomalous threshold, so it bypassed the velocity flag. However, the 11,000 km jump is clearly artificial.

## 3. Conclusions and Recommendations for ML Sequence Generation
The investigation confirms that extreme anomalies are caused by data telemetry errors rather than physical iceberg behavior. 

**Recommendations:**
1. **Zero-Coordinate Filter:** Before sequence generation, drop any rows where `latitude == 0.0` and `longitude == 0.0`. These are effectively "null" coordinates that cause artificial 10,000+ km distance jumps.
2. **Trajectory Splitting:** Do not interpolate over massive coordinate jumps (like `a74a`'s 2,000 km jump). When an `ANOMALOUS_VELOCITY` is encountered, the ML pipeline should **split** the trajectory at that point into two separate, independent sequences. If either sequence is too short (e.g. < 5 observations), it should be discarded.
3. **Distance Thresholds:** Consider adding an absolute distance jump threshold (e.g., > 100 km) in addition to velocity, to catch anomalies over very long time gaps that slip past the velocity threshold (like `a76`).
