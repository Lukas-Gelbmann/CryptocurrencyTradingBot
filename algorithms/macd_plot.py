import matplotlib.pyplot as plt
import pandas
from mpl_finance import candlestick_ohlc
from algorithm_interface import AlgorithmInterface

FASTPERIOD = 12
SLOWPERIOD = 26
SIGNALPERIOD = 9


# class to demonstrate how the MACD is calculated
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
        plt.style.use('ggplot')
        df = pandas.DataFrame(new_history)
        df = df.iloc[:, [0, 1, 2, 3, 4]]
        df = df[:100]
        df = df.apply(lambda x: x * 10000)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close']
        for index in range(len(new_history)):
            df['Date'][index] = index

        print(df)

        # calculate
        exp1 = df['Close'].ewm(span=FASTPERIOD, adjust=False).mean()
        exp2 = df['Close'].ewm(span=SLOWPERIOD, adjust=False).mean()
        dfmacd = exp1 - exp2
        dfsignal = dfmacd.ewm(span=SIGNALPERIOD, adjust=False).mean()
        # to numpy to check if buy or sell
        e1 = exp1.to_numpy()
        e2 = exp2.to_numpy()
        macd = dfmacd.to_numpy()
        signal = dfsignal.to_numpy()
        fig, axs = plt.subplots(2)

        candlestick_ohlc(axs[0], df.values, width=0.5, colorup='green', colordown='red')
        axs[0].plot(e1, label='Exp. MA mit 12 Werten')
        axs[0].plot(e2, label='Exp. MA mit 26 Werten')
        axs[0].legend(loc='lower left')

        axs[1].plot(macd, label='MACD')
        axs[1].plot(signal, label='Signal (Exp. MA des MACD mit 9 Werten)')
        axs[1].legend(loc='lower left')
        fig.tight_layout()
        plt.show()
        exit(0)
