class RiskEngine:

    def calculate_risk(self, driver_data, imu_data, vehicle_data):

        drowsiness_score = float(
            driver_data.get("drowsiness_score", 0)
        )

        distraction = driver_data.get(
            "distraction_detected", False
        )

        speed = float(
            vehicle_data.get("speed", 0)
        )

        acceleration = float(
            vehicle_data.get("acceleration", 0)
        )

        steering_angle = abs(
            float(vehicle_data.get("steering_angle", 0))
        )

        risk_score = drowsiness_score

        # Distraction
        if distraction:
            risk_score += 20

        # High speed
        if speed > 80:
            risk_score += 15

        # Sudden acceleration / deceleration
        if abs(acceleration) > 2:
            risk_score += 10

        # Large steering movement
        if steering_angle > 25:
            risk_score += 10

        # Limit score
        risk_score = min(risk_score, 100)

        # Risk level
        if risk_score >= 70:
            risk_level = "HIGH"

        elif risk_score >= 40:
            risk_level = "MODERATE"

        else:
            risk_level = "LOW"

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level
        }