
__version__ = "0.9.3.99"
__version__bak = __version__


import os
import copy
import logging

from pathlib import Path

from .log import get_module_logger

# init qlib
def init(default_conf="client", **kwargs):
    from .config import C
    from .data.cache import H

    logger = get_module_logger("Initialization")

    skip_if_reg = kwargs.pop("skip_if_reg", False)
    if skip_if_reg and C.registered:
        logger.warning("qlib has been initialized, skip init")
        return

    clear_mem_cache = kwargs.pop("clear_mem_cache", True)
    if clear_mem_cache:
        H.clear()
    
    C.set(default_conf, **kwargs)
    get_module_logger.setLevel(C.logging_level)

    # mount nfs
    for _freq, provider_uri in C.provider_uri.items():
        logger.info(f"{_freq}, {provider_uri}")
        mount_path = C["mount_path"][_freq]
        # check path if server/local
        uri_type = C.dpm.get_uri_type(provider_uri)
        if uri_type == C.LOCAL_URI:
            if not Path(provider_uri).exists():
                if C["auto_mount"]:
                    logger.error(f"Invalid provider_uri: {provider_uri}, please check if a valid provider_uri is has been set. This path does not exist.")
                else:
                    logger.warning(f"auth_path is False, please make sure {mount_path} is mounted")
        elif uri_type == C.NFS_URI:
            pass
        else:
            raise NotImplementedError(f"Unknown uri type: {uri_type}")
    
    C.register()


    