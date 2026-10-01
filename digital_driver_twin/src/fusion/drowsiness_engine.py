# ==================================================
# DIGITAL DRIVER TWIN
# DROWSINESS ENGINE
# ==================================================


class DrowsinessEngine:

    def __init__(self):

        # ------------------------------------------
        # Weights
        # ------------------------------------------

        self.perclos_weight = 0.50

        self.yawn_weight = 0.20

        self.head_pose_weight = 0.30


    # ==================================================
    # PERCLOS SCORE
    # ==================================================

    def calculate_perclos_score(self, perclos):

        if perclos < 10:

            return 0.0

        elif perclos < 20:

            return 0.3

        elif perclos < 30:

            return 0.6

        else:

            return 1.0


    # ==================================================
    # YAWN SCORE
    # ==================================================

    def calculate_yawn_score(self, yawn_count):

        if yawn_count == 0:

            return 0.0

        elif yawn_count <= 2:

            return 0.3

        elif yawn_count <= 4:

            return 0.6

        else:

            return 1.0


    # ==================================================
    # HEAD POSE SCORE
    # ==================================================

    def calculate_head_pose_score(
        self,
        pitch,
        yaw,
        roll
    ):

        # Absolute angles

        pitch = abs(pitch)

        yaw = abs(yaw)

        roll = abs(roll)


        # Check abnormal head movement

        abnormal_axes = 0


        if pitch > 20:

            abnormal_axes += 1


        if yaw > 25:

            abnormal_axes += 1


        if roll > 20:

            abnormal_axes += 1


        # Convert to score

        if abnormal_axes == 0:

            return 0.0

        elif abnormal_axes == 1:

            return 0.4

        elif abnormal_axes == 2:

            return 0.7

        else:

            return 1.0


    # ==================================================
    # FINAL DROWSINESS SCORE
    # ==================================================

    def calculate_score(
        self,
        perclos,
        yawn_count,
        pitch,
        yaw,
        roll
    ):

        # Individual scores

        perclos_score = (
            self.calculate_perclos_score(
                perclos
            )
        )


        yawn_score = (
            self.calculate_yawn_score(
                yawn_count
            )
        )


        head_pose_score = (
            self.calculate_head_pose_score(
                pitch,
                yaw,
                roll
            )
        )


        # ------------------------------------------
        # Weighted fusion
        # ------------------------------------------

        final_score = (

            perclos_score
            * self.perclos_weight

            +

            yawn_score
            * self.yawn_weight

            +

            head_pose_score
            * self.head_pose_weight

        )


        # Convert to percentage

        final_score *= 100


        return final_score


    # ==================================================
    # DROWSINESS LEVEL
    # ==================================================

    def get_drowsiness_level(
        self,
        score
    ):

        if score < 30:

            return "LOW"

        elif score < 60:

            return "MODERATE"

        else:

            return "HIGH"