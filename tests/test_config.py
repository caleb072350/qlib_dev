
import unittest
import logging

from qlib.config import Config
from qlib.config import _default_config
from qlib.config import C

from qlib.utils.mod import split_module_path
from qlib.log import get_module_logger
from qlib.log import set_log_with_config

from qlib.utils import can_use_cache

from qlib.data.data import ProviderBackendMixin

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.default_conf = _default_config
        self.config = Config(self.default_conf)
    
    def test_default_config(self):
        self.assertEqual(self.config._default_conf, self.default_conf)
    
    def test_split_module_path(self):
        module_path = "qlib.config.Config"
        module, cls = split_module_path(module_path)
        self.assertEqual(module, "qlib.config")
        self.assertEqual(cls, "Config")

    def test_module_logger(self):
        set_log_with_config(C.logging_config)
        logger = get_module_logger("test", logging.DEBUG)
        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")

    def test_can_use_cache(self):
        set_log_with_config(C.logging_config)
        logger = get_module_logger("test", logging.DEBUG)
        self.assertEqual(can_use_cache(), True)
        if can_use_cache():
            logger.info("can use cache")
    
    def test_is_depend_redis(self):
        set_log_with_config(C.logging_config)
        logger = get_module_logger("test", logging.DEBUG)
        if C.is_depend_redis("DiskDatasetCache"):
            logger.info("is depend redis")

    def test_data(self):
        provider = ProviderBackendMixin()
        backend = provider.get_default_backend()
        print(backend)
        

if __name__ == '__main__':
    unittest.main()
    
