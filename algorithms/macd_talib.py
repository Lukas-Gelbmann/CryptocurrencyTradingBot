from algorithm_interface import AlgorithmInterface
import talib


class Algorithm(AlgorithmInterface):
    FASTPERIOD = 12
    SLOWPERIOD = 26
    SIGNALPERIOD = 9

    def get_possible_parameters(self):
        return [[2, 16], [17, 60], [2, 16]]

    def get_standard_parameters(self):
        return [self.FASTPERIOD, self.SLOWPERIOD, self.SIGNALPERIOD]

    def init_algorithm(self, parameter=None):
        if parameter is not None:
            self.FASTPERIOD = int(parameter[0])
            self.SLOWPERIOD = int(parameter[1])
            self.SIGNALPERIOD = int(parameter[2])

    def on_new_data(self, new_history):
        macd, signal, hist = talib.MACD(new_history[:, 4], fastperiod=self.FASTPERIOD, slowperiod=self.SLOWPERIOD,
                                        signalperiod=self.SIGNALPERIOD)

        newmacd = macd[len(macd) - 2]
        oldmacd = macd[len(macd) - 3]
        newsignal = signal[len(macd) - 2]
        oldsignal = signal[len(macd) - 3]

        if oldmacd > oldsignal and newmacd < newsignal:
            return self.framework.SELL
        if oldmacd < oldsignal and newmacd > newsignal:
            return self.framework.BUY
        return
