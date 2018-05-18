%matplotlib inline
import numpy as np
import matplotlib.pyplot as plt

def plot_time_series(values):
    print(values.shape)
    for col in values.T:
        plt.plot(col)
    plt.show()