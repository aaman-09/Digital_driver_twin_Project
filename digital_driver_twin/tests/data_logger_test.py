from src.fusion.data_logger import DataLogger


logger = DataLogger(
    "data/processed/test_driver_session.csv"
)


logger.log(
    ear=0.31,
    perclos=5.2,
    mar=0.32,
    yawns=1,
    pitch=2.4,
    yaw=-3.1,
    roll=1.2,
    drowsiness_score=18.5,
    risk_level="LOW"
)


print("Data logging test completed.")