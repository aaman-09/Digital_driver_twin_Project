from src.fusion.drowsiness_engine import DrowsinessEngine


engine = DrowsinessEngine()


score = engine.calculate_score(

    perclos=35,

    yawn_count=3,

    pitch=25,

    yaw=5,

    roll=2
)


level = engine.get_drowsiness_level(score)


print("==============================")
print("DIGITAL DRIVER TWIN")
print("==============================")

print(f"Drowsiness Score: {score:.2f}%")

print(f"Drowsiness Level: {level}")

print("==============================")