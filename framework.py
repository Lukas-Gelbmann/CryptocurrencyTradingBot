import ccxt
import csv
import json
import numpy
import pprint
import time
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import brute
from geneticalgorithm import geneticalgorithm as ga
from algorithms.buy import Buy
from algorithms.sell import Sell
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram_implementation import Telegram


class Framework:
    BUY = 'buy'
    SELL = 'sell'

    def __init__(self):
        f = open('config.json')
        config = json.load(f)
        self.history = []
        self.telegramEnabled = config['run']['telegram']['enabled']
        self.telegramToken = config['run']['telegram']['token']
        self.historyFilename = config['backtest']['filename']
        self.fee = config['backtest']['fee']
        self.withFees = config['optimize']['withFees']
        self.mode = config['mode']
        self.since = config['fetchHistory']['since']
        self.fetchHistoryFilename = config['fetchHistory']['filename']
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
            self.loadedHistory = numpy.genfromtxt(self.historyFilename, delimiter=',')
        except:
            print("No history available")

        mod = __import__('algorithms.' + self.module, fromlist=[self.classname])
        self.algorithm = getattr(mod, 'Algorithm')
        self.algorithm.framework = self

    def get_holdings(self):
        all_balances = self.exchange.fetch_balance()['free']
        pprint.pprint(all_balances)
        return all_balances

    def fetch_new_history(self, since=None):
        self.history = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=since)
        return self.history

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

    def start_bot(self):
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
            history = self.fetch_new_history()
            if history[len(history) - 1][0] != last_timestamp:
                # new timestamp = new data
                last_timestamp = history[len(history) - 1][0]
                side = algorithm.on_new_data(algorithm, numpy.array(history))
                if side is self.SELL or side is self.BUY:
                    self.execute_trade(side, telegram=telegram)

    def init_telegram(self):
        if not self.telegramEnabled:
            return

        updater = Updater(self.telegramToken, use_context=True)
        dispatcher = updater.dispatcher
        telegram = Telegram(framework=self)
        dispatcher.add_handler(CommandHandler("start", telegram.start))
        dispatcher.add_handler(CommandHandler("stop", telegram.stop))
        dispatcher.add_handler(CommandHandler("help", telegram.help))
        dispatcher.add_handler(CommandHandler("status", telegram.status))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, telegram.response))
        updater.start_polling()
        return telegram

    def load_historical_data(self):
        # download
        print("downloading...")
        history = self.fetch_new_history(since=self.since * 1000)
        lasttimestamp = 1
        thistimestamp = 0
        while lasttimestamp != thistimestamp:
            time.sleep(self.exchange.rateLimit / 1000)
            lasttimestamp = history[len(history) - 1][0]
            history = history + self.fetch_new_history(since=lasttimestamp + 1)
            thistimestamp = history[len(history) - 1][0]

        pprint.pprint(history)
        print("Length: " + str(len(history)))
        # save
        csvfile = open(self.fetchHistoryFilename, "w", newline="")
        writer = csv.writer(csvfile, delimiter=",")
        for candlestick in history:
            writer.writerow(candlestick)
        csvfile.close()
        print("finished")

    def back_test(self, fee, otheralgorithm=None):
        history = self.loadedHistory
        if otheralgorithm is None:
            algorithm = self.algorithm
        else:
            algorithm = otheralgorithm
        algorithm.framework = self
        algorithm.init_algorithm(algorithm)
        basecur = 1
        quotecur = 0
        dates = []
        price = []
        buydates = []
        buyprice = []
        selldates = []
        sellprice = []
        for x in range(500, len(history)):
            date = datetime.fromtimestamp(history[x][0] / 1000)
            dates.append(date)
            side = algorithm.on_new_data(algorithm, history[x - 500:x])
            curvalue = basecur + quotecur / history[x][4]
            if side == self.SELL:
                quotecur = quotecur + history[x][4] * basecur * (1 - fee / 100)
                basecur = 0
                selldates.append(date)
                sellprice.append(curvalue)
            if side == self.BUY:
                basecur = basecur + quotecur / history[x][4] * (1 - fee / 100)
                quotecur = 0
                buydates.append(date)
                buyprice.append(curvalue)
            price.append(curvalue)
        return (dates, price), (selldates, sellprice), (buydates, buyprice)

    def backtesting(self):
        print("backtesting...")
        # gather tests
        backtests = [self.back_test(0), self.back_test(self.fee), self.back_test(self.fee, Buy),
                     self.back_test(self.fee, Sell)]
        info = ['without fees', 'with fees', 'after buy at start', 'after sell at start']

        # plot
        i = 0
        for backtest in backtests:
            print("You have {0}% of your initial portfolio after {1} trades ({2})".format(
                str(backtest[0][1][-1] * 100), str(len(backtest[1][0]) + len(backtest[2][0])), info[i]))
            plt.plot(backtest[0][0], backtest[0][1], label='Portfolio in base currency ' + info[i])
            if i == 3:
                plt.plot(backtest[1][0], backtest[1][1], 'ro', label='SELL the base currency')
                plt.plot(backtest[2][0], backtest[2][1], 'go', label='BUY the base currency')
            else:
                plt.plot(backtest[1][0], backtest[1][1], 'ro')
                plt.plot(backtest[2][0], backtest[2][1], 'go')
            i = i + 1
        plt.gcf().autofmt_xdate()
        plt.legend(loc='upper left')
        plt.show()

    def fitness(self, parameters):
        history = self.loadedHistory
        algorithm = self.algorithm
        fee = 0
        if self.withFees:
            fee = self.fee
        algorithm.init_algorithm(algorithm, parameters)
        basecur = 1
        quotecur = 0
        for x in range(500, len(history)):
            side = algorithm.on_new_data(algorithm, history[x - 500:x])
            if side == self.SELL:
                quotecur = quotecur + history[x][4] * basecur * (1 - fee / 100)
                basecur = 0
            if side == self.BUY:
                basecur = basecur + quotecur / history[x][4] * (1 - fee / 100)
                quotecur = 0
        result = basecur + quotecur / history[-1][4]
        return 1 / result

    def optimize_genetic(self):
        print("optimizing via genetic alg...")
        algorithm_param = {'max_num_iteration': 1000,
                           'population_size': 100,
                           'mutation_probability': 0.1,
                           'elit_ratio': 0.01,
                           'crossover_probability': 0.5,
                           'parents_portion': 0.3,
                           'crossover_type': 'uniform',
                           'max_iteration_without_improv': 50}
        bnds = numpy.array(self.algorithm.get_possible_parameters(self.algorithm))
        model = ga(function=self.fitness, dimension=3, variable_type='int', variable_boundaries=bnds,
                   algorithm_parameters=algorithm_param)
        val = model.run()
        print(val)

    def optimize_brute_force(self):
        print("optimizing via scipy minimize optimization...")
        bnds = numpy.array(self.algorithm.get_possible_parameters(self.algorithm))
        sol = brute(self.fitness, bnds)
        print(sol)
        print()

    def what_to_start(self):
        if self.mode == "run":
            self.start_bot()
        if self.mode == "backtest":
            self.backtesting()
        if self.mode == "fetchHistory":
            self.load_historical_data()
        if self.mode == "optimize":
            self.optimize_genetic()
            self.optimize_brute_force()
