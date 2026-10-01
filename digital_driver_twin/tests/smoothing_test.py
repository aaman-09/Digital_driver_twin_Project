from src.fusion.smoothing import ExponentialSmoother


smoother = ExponentialSmoother(alpha=0.2)


test_values = [
    10,
    12,
    15,
    70,
    72,
    75,
    20,
    18
]


print("==============================")
print("TEMPORAL SMOOTHING TEST")
print("==============================")


for value in test_values:

    smoothed = smoother.update(value)

    print(
        f"Raw: {value:>5.1f}  "
        f"Smoothed: {smoothed:>6.2f}"
    )


print("==============================")