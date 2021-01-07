import numpy as np
from algorithm_interface import AlgorithmInterface


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
        fastema = exponentialMovingAverage(new_history[:, 4], self.FASTPERIOD)
        slowema = exponentialMovingAverage(new_history[:, 4], self.SLOWPERIOD)

        # cut the front where no calculation happened
        fastema = fastema[self.SLOWPERIOD:]
        slowema = slowema[self.SLOWPERIOD:]

        # subtract lists using numpy
        macd = list(np.array(fastema) - np.array(slowema))
        signal = exponentialMovingAverage(macd, self.SIGNALPERIOD)

        # buy and sell strategy
        newmacd = macd[-1]
        oldmacd = macd[-2]
        newsignal = signal[-1]
        oldsignal = signal[-2]
        if oldmacd > oldsignal and newmacd < newsignal:
            return self.framework.SELL
        if oldmacd < oldsignal and newmacd > newsignal:
            return self.framework.BUY
        return
