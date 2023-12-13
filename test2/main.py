from qlib.log import set_log_with_config
from qlib.config import C
import logging
from qlib.log import get_module_logger
from qlib.utils import can_use_cache
import qlib 
if __name__ == "__main__":

    qlib.init(provider_uri="qlib_data/cn_data")
    
    set_log_with_config(C.logging_config)
    logger = get_module_logger("test", logging.DEBUG)
    if can_use_cache():
        logger.info("can use cache")