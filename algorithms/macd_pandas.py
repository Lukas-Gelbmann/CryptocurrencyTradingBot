from algorithm_interface import AlgorithmInterface
import pandas


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
        # to dataframe
        df = pandas.DataFrame(new_history)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close']
        closes = df['Close']

        # calculate
        fast_ema = closes.ewm(span=self.FASTPERIOD, adjust=False).mean()
        slow_ema = closes.ewm(span=self.SLOWPERIOD, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=self.SIGNALPERIOD, adjust=False).mean()

        # to numpy to check if buy or sell
        macd = macd.to_numpy()
        signal = signal.to_numpy()

        newmacd = macd[- 1]
        oldmacd = macd[- 2]
        newsignal = signal[- 1]
        oldsignal = signal[- 2]
        if oldmacd > oldsignal and newmacd < newsignal:
            return self.framework.SELL
        if oldmacd < oldsignal and newmacd > newsignal:
            return self.framework.BUY
        return
