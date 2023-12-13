import os
print(os.getcwd())

from tests.data import GetData
from qlib.constant import REG_CN


def load_data():
    provider_uri = "qlib_data/cn_data"
    GetData().qlib_data(target_dir=provider_uri, region=REG_CN, exists_skip=True)

if __name__ == "__main__":
    load_data()
