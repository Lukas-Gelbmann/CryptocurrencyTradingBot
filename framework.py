import ccxt
import csv
import json
import numpy
import pprint
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import brute
from geneticalgorithm import geneticalgorithm as ga
from algorithms.buy import Buy
from algorithms.sell import Sell
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram_implementation import Telegram
from mpl_finance import candlestick_ohlc


# main part of the project
class Framework:
    # static variables for buying and selling
    BUY = 'buy'
    SELL = 'sell'

    # load the config information into global variables
    def __init__(self):
        f = open('config.json')
        config = json.load(f)
        self.telegram_enabled = config['run']['telegram']['enabled']
        self.telegram_token = config['run']['telegram']['token']
        self.fee = config['fee']
        self.mode = config['mode']
        self.since = config['fetchHistory']['since']
        self.fetch_filename = config['fetchHistory']['filename']
        self.module = config['algorithmModule']
        self.classname = config['algorithmClassName']
        self.timeframe = config['timeframe']
        self.test = config['run']['test']
        self.amount = config['run']['amount']
        self.symbol = config['tradingpair']
        self.exchange = getattr(ccxt, config['exchange'])({
            'apiKey': config['login']['apiKey'],
            'secret': config['login']['secret'],
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })
        try:
            self.loaded_history = numpy.genfromtxt(config['history'], delimiter=',')
        except:
            print("No history available")
        mod = __import__('algorithms.' + self.module, fromlist=[self.classname])
        self.algorithm = getattr(mod, 'Algorithm')
        self.algorithm.framework = self

    # helper function to get information about holdings (telegram)
    def get_holdings(self):
        all_balances = self.exchange.fetch_balance()['free']
        pprint.pprint(all_balances)
        return all_balances

    # helper function to fetch history
    def fetch_ohlcv(self, since=None):
        return self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=since)

    # helper function to execute trade
    def execute_trade(self, side, telegram=None):
        typ = 'market'
        price = None
        params = {'test': self.test}
        order = self.exchange.create_order(self.symbol, typ, side, self.amount, price, params)
        print(order)
        if telegram is not None and telegram.messaging is not None:
            telegram.messaging.reply_text(order)
        # telegram
        return order

    # method to initialize all the telegram features
    def init_telegram(self):
        if not self.telegram_enabled:
            return
        updater = Updater(self.telegram_token, use_context=True)
        dispatcher = updater.dispatcher
        telegram = Telegram(framework=self)
        dispatcher.add_handler(CommandHandler("start", telegram.start))
        dispatcher.add_handler(CommandHandler("stop", telegram.stop))
        dispatcher.add_handler(CommandHandler("help", telegram.help))
        dispatcher.add_handler(CommandHandler("status", telegram.status))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, telegram.response))
        updater.start_polling()
        return telegram

    # execute the bot in real time
    def run(self):
        print("starting bot...")
        telegram = self.init_telegram()
        # init algorithm
        mod = __import__('algorithms.' + self.module, fromlist=[self.classname])
        algorithm = getattr(mod, 'Algorithm')
        algorithm.framework = self
        algorithm.init_algorithm(algorithm)

        last_timestamp = 0
        while True:
            time.sleep(self.exchange.rateLimit / 1000)
            history = self.fetch_ohlcv()
            if history[len(history) - 1][0] != last_timestamp:
                # new timestamp = new data
                last_timestamp = history[len(history) - 1][0]
                side = algorithm.on_new_data(algorithm, numpy.array(history))
                if side is self.SELL or side is self.BUY:
                    self.execute_trade(side, telegram=telegram)

    # method to fetch history into a file
    def fetch_history(self):
        # download
        print("downloading...")
        history = self.fetch_ohlcv(since=self.since * 1000)
        last_timestamp = 1
        this_timestamp = 0
        while last_timestamp != this_timestamp:
            time.sleep(self.exchange.rateLimit / 1000)
            print(history)
            last_timestamp = history[-1][0]
            history = history + self.fetch_ohlcv(since=last_timestamp + 1)
            this_timestamp = history[-1][0]

        pprint.pprint(history)
        print("Length: " + str(len(history)))
        # save
        csv_file = open(self.fetch_filename, "w", newline="")
        writer = csv.writer(csv_file, delimiter=",")
        for candlestick in history:
            writer.writerow(candlestick)
        csv_file.close()
        print("finished")

    # method to visually show history from specific file
    def show_history(self):
        print("showing history...")
        df = pd.DataFrame(self.loaded_history)
        for index in range(len(df)):
            df[0][index] = index
        plt.style.use('ggplot')
        fig, ax = plt.subplots()
        candlestick_ohlc(ax, df.values, width=0.5, colorup='green', colordown='red')
        plt.show()

    # helper method to execute a single back test, returns all the parameters to create a graph
    def backtest_execution(self, fee, other_algorithm=None):
        history = self.loaded_history
        if other_algorithm is None:
            algorithm = self.algorithm
        else:
            algorithm = other_algorithm
        algorithm.framework = self
        algorithm.init_algorithm(algorithm)
        base_currency = 1
        quote_currency = 0
        dates = []
        price = []
        buy_dates = []
        buy_price = []
        sell_dates = []
        sell_price = []
        for x in range(500, len(history)):
            date = datetime.fromtimestamp(history[x][0] / 1000)
            dates.append(date)
            side = algorithm.on_new_data(algorithm, history[x - 500:x])
            current_value = base_currency + quote_currency / history[x][4]
            if side == self.SELL:
                quote_currency += history[x][4] * base_currency * (1 - fee / 100)
                base_currency = 0
                sell_dates.append(date)
                sell_price.append(current_value)
            if side == self.BUY:
                base_currency += quote_currency / history[x][4] * (1 - fee / 100)
                quote_currency = 0
                buy_dates.append(date)
                buy_price.append(current_value)
            price.append(current_value)
        return (dates, price), (sell_dates, sell_price), (buy_dates, buy_price)

    # method that executes all important backtests with the algorithm and visualizes the result
    def backtest(self):
        print("backtesting...")
        # gather tests
        backtests = [self.backtest_execution(self.fee, Buy), self.backtest_execution(self.fee, Sell),
                     self.backtest_execution(0), self.backtest_execution(self.fee)]
        base = self.symbol.split("/")[0]
        quote = self.symbol.split("/")[1]
        info = ['buy and hold of ' + base, 'buy and hold of ' + quote, 'algorithm, without fees',
                'algorithm, with fees']
        # plot
        i = 0
        for backtest in backtests:
            print("You have {0}% of your initial portfolio after {1} trades ({2})".format(
                str(backtest[0][1][-1] * 100), str(len(backtest[1][0]) + len(backtest[2][0])), info[i]))
            # plt.plot(backtest[0][0], backtest[0][1], label='Portfolio in ' + base + ' ' + info[i])
            plt.plot(backtest[0][0], backtest[0][1], label=info[i])
            if i == 3:
                plt.plot(backtest[1][0], backtest[1][1], 'ro', label='SELL ' + base + ' for ' + quote)
                plt.plot(backtest[2][0], backtest[2][1], 'go', label='BUY ' + base + ' for ' + quote)
            else:
                plt.plot(backtest[1][0], backtest[1][1], 'ro')
                plt.plot(backtest[2][0], backtest[2][1], 'go')
            i = i + 1
        plt.ylabel(base)
        # plt.title("Backtest of " + self.module + " " + str(self.algorithm.get_standard_parameters(self.algorithm)))
        plt.gcf().autofmt_xdate()
        plt.legend(loc='upper left')
        plt.show()

    # more efficient backtesting function, that only tracks the profit
    # -> used for optimization -> return 1 / result because you want max instead of min
    def fitness(self, parameters):
        history = self.loaded_history
        algorithm = self.algorithm
        fee = self.fee

        algorithm.init_algorithm(algorithm, parameters)
        base_currency = 1
        quote_currency = 0
        for x in range(500, len(history)):
            side = algorithm.on_new_data(algorithm, history[x - 500:x])
            if side == self.SELL:
                quote_currency = quote_currency + history[x][4] * base_currency * (1 - fee / 100)
                base_currency = 0
            if side == self.BUY:
                base_currency = base_currency + quote_currency / history[x][4] * (1 - fee / 100)
                quote_currency = 0
        result = base_currency + quote_currency / history[-1][4]
        return 1 / result

    # method that optimizes the fitness function via genetic algorithm
    def optimize_genetic(self):
        print("optimizing via genetic alg...")
        algorithm_param = {'max_num_iteration': 1000,
                           'population_size': 100,
                           'mutation_probability': 0.1,
                           'elit_ratio': 0.01,
                           'crossover_probability': 0.5,
                           'parents_portion': 0.3,
                           'crossover_type': 'uniform',
                           'max_iteration_without_improv': 100}

        bounds = self.algorithm.get_possible_parameters(self.algorithm)
        model = ga(function=self.fitness, dimension=len(bounds), variable_type=type(bounds[0][0]).__name__,
                   variable_boundaries=numpy.array(bounds), algorithm_parameters=algorithm_param)
        val = model.run()
        print(val)

    # method that optimizes the fitness function by trying all possibilities
    def optimize_brute_force(self):
        print("optimizing via scipy minimize optimization...")
        bounds = numpy.array(self.algorithm.get_possible_parameters(self.algorithm))
        sol = brute(self.fitness, bounds)
        print(sol)
        print()

    # method that starts the correct part of the program
    def what_to_start(self):
        if self.mode == "run":
            self.run()
        if self.mode == "fetchHistory":
            self.fetch_history()
        if self.mode == "showHistory":
            self.show_history()
        if self.mode == "backtest":
            self.backtest()
        if self.mode == "optimize":
            self.optimize_genetic()
            self.optimize_brute_force()
