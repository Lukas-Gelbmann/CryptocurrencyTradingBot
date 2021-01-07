from algorithm_interface import AlgorithmInterface
import pandas
import talib
import numpy as np
import matplotlib.pyplot as plt


def exponentialMovingAverage(values, window):
    result = []
    for x in range(window - 1):
        result.append(0)
    # get first sma for window size to start
    sma = sum(values[:window]) / window
    result.append(sma)

    multiplier = 2 / float(1 + window)
    for value in values[window:]:
        # EMA(current) = ( (Price(current) - EMA(prev) ) x Multiplier) + EMA(prev)
        ema = ((value - result[-1]) * multiplier) + result[-1]
        result.append(ema)
    return result


# class to demonstrate that manual, pandas and talib implementation are the same
class Algorithm(AlgorithmInterface):
    FASTPERIOD = 12
    SLOWPERIOD = 26
    SIGNALPERIOD = 9

    def get_possible_parameters(self):
        return [[2, 16], [16, 40], [2, 16]]

    def get_standard_parameters(self):
        return [self.FASTPERIOD, self.SLOWPERIOD, self.SIGNALPERIOD]

    def init_algorithm(self, parameter=None):
        if parameter is not None:
            self.FASTPERIOD = int(parameter[0])
            self.SLOWPERIOD = int(parameter[1])
            self.SIGNALPERIOD = int(parameter[2])

    def on_new_data(self, new_history):
        # pandas
        df = pandas.DataFrame(new_history[:, 4])
        exp1 = df.ewm(span=self.FASTPERIOD, adjust=False).mean()
        exp2 = df.ewm(span=self.SLOWPERIOD, adjust=False).mean()
        dfmacd = exp1 - exp2
        macd_pandas = dfmacd.to_numpy()
        dfsignal = dfmacd.ewm(span=self.SIGNALPERIOD, adjust=False).mean()
        signal_pandas = dfsignal.to_numpy()
        macd_pandas = macd_pandas[self.SLOWPERIOD:]
        signal_pandas = signal_pandas[self.SLOWPERIOD:]

        # ta lib
        macd_ta, signal_ta, hist = talib.MACD(new_history[:, 4], fastperiod=self.FASTPERIOD, slowperiod=self.SLOWPERIOD,
                                              signalperiod=self.SIGNALPERIOD)
        macd_ta = macd_ta[self.SLOWPERIOD:]
        signal_ta = signal_ta[self.SLOWPERIOD:]

        # manual
        fastema = exponentialMovingAverage(new_history[:, 4], self.FASTPERIOD)
        slowema = exponentialMovingAverage(new_history[:, 4], self.SLOWPERIOD)
        fastema = fastema[self.SLOWPERIOD:]
        slowema = slowema[self.SLOWPERIOD:]
        macd_man = list(np.array(fastema) - np.array(slowema))
        signal_man = exponentialMovingAverage(macd_man, self.SIGNALPERIOD)

        # plot
        plt.plot(macd_pandas, label='MACD Pandas')
        plt.plot(macd_ta, label='MACD TA-Lib')
        plt.plot(macd_man, label='MACD Manual')
        plt.plot(signal_pandas, label='Signal Pandas')
        plt.plot(signal_ta, label='Signal TA-Lib')
        plt.plot(signal_man, label='Signal Manual')
        plt.legend(loc='upper left')
        plt.show()
        exit(0)
