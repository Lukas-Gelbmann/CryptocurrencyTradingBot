from algorithm_interface import AlgorithmInterface


class Buy(AlgorithmInterface):
    bought = False

    def get_possible_parameters(self):
        return []

    def get_standard_parameters(self):
        return []

    def init_algorithm(self, parameter=None):
        pass

    def on_new_data(self, new_history):
        if self.bought:
            return
        self.bought = True
        return self.framework.BUY
