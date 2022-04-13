from .gsc_trading_data_utils import GSCUtils

class RBYUtils(GSCUtils):
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    base_folder = "useful_data/rby/"
    num_stats = 5
    
    def __init__(self):
        super(RBYUtils, self).__init__()