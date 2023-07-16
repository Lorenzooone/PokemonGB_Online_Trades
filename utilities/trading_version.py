class TradingVersion:
    """
    Class which contains the version and the version's helper methods.
    """

    version_major = 4
    version_minor = 0
    version_build = 0
    
    def read_version_data(data):
        ret = []
        for i in range(3):
            ret += [data[i * 2] + (data[(i * 2) + 1] << 8)]
        return ret
    
    def prepare_version_data():
        ret = []
        ret += [TradingVersion.version_major & 0xFF, (TradingVersion.version_major >> 8) & 0xFF]
        ret += [TradingVersion.version_minor & 0xFF, (TradingVersion.version_minor >> 8) & 0xFF]
        ret += [TradingVersion.version_build & 0xFF, (TradingVersion.version_build >> 8) & 0xFF]
        return ret

