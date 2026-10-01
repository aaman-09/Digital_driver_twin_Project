# ==================================================
# DIGITAL DRIVER TWIN
# TEMPORAL SMOOTHING
# ==================================================


class ExponentialSmoother:

    def __init__(self, alpha=0.2):

        # Alpha controls how quickly
        # the output reacts to new values.

        self.alpha = alpha

        self.value = None


    def update(self, new_value):

        # First value

        if self.value is None:

            self.value = new_value

        else:

            self.value = (
                self.alpha * new_value
                +
                (1 - self.alpha) * self.value
            )


        return self.value