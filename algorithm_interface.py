import abc


class AlgorithmInterface:

    def __init__(self):
        self.framework = None

    @abc.abstractmethod
    def init_algorithm(self, parameter=None):
        pass  # init stuff

    @abc.abstractmethod
    def on_new_data(self, new_history):
        pass  # return self.framework.BUY

    @abc.abstractmethod
    def get_standard_parameters(self):
        pass  # return list with standard parameters for the algorithm

    @abc.abstractmethod
    def get_possible_parameters(self):
        pass  # return list of list with ranges of all parameters that can be fitted to the algorithm
