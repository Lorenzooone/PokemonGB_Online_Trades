from .gsc_trading_data_utils import GSCUtils

class RBYUtils(GSCUtils):
    """
    Class which contains generic methods and data used for
    pokémon-related functions.
    """
    no_mail_path = "useful_data/no_mail_section_rby.bin"
    
    def __init__(self):
        super(RBYUtils, self).__init__()