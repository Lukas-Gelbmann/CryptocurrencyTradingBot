from algorithm_interface import AlgorithmInterface
import talib

class Algorithm(AlgorithmInterface):
    OVERBOUGHT = 70
    OVERSOLD = 30
    PERIOD = 14
    FASTPERIOD = 12
    SLOWPERIOD = 26
    SIGNALPERIOD = 9
    last_operation = ""

    def get_possible_parameters(self):
        return [[60, 90], [10, 40], [3, 30], [2, 16], [17, 60], [2, 16]]

    def get_standard_parameters(self):
        return [self.OVERBOUGHT, self.OVERSOLD, self.PERIOD, self.FASTPERIOD, self.SLOWPERIOD, self.SIGNALPERIOD]

    def init_algorithm(self, parameter=None):
        self.last_operation = self.framework.BUY
        if parameter is not None:
            self.OVERBOUGHT = parameter[0]
            self.OVERSOLD = parameter[1]
            self.PERIOD = parameter[2]
            self.FASTPERIOD = int(parameter[3])
            self.SLOWPERIOD = int(parameter[4])
            self.SIGNALPERIOD = int(parameter[5])

    def on_new_data(self, new_history):
        rsi = talib.RSI(new_history[:, 4], self.PERIOD)
        value = rsi[-1]
        macd, signal, hist = talib.MACD(new_history[:, 4], fastperiod=self.FASTPERIOD, slowperiod=self.SLOWPERIOD,
                                        signalperiod=self.SIGNALPERIOD)

        newmacd = macd[len(macd) - 2]
        oldmacd = macd[len(macd) - 3]
        newsignal = signal[len(macd) - 2]
        oldsignal = signal[len(macd) - 3]

        if oldmacd > oldsignal and newmacd < newsignal:
            self.last_operation = self.framework.SELL
            return self.framework.SELL
        if oldmacd < oldsignal and newmacd > newsignal:
            self.last_operation = self.framework.BUY
            return self.framework.BUY

        if value > self.OVERBOUGHT and self.last_operation == self.framework.BUY:
            self.last_operation = self.framework.SELL
            return self.framework.SELL

        if value < self.OVERSOLD and self.last_operation == self.framework.SELL:
            self.last_operation = self.framework.BUY
            return self.framework.BUY
        return
