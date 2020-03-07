import config_default

configs = config_default.configs

def revise(old_config,new_config):
    for k,v in old_config.items():
        if k in new_config.keys():
            if isinstance(v,dict):
                revise(v,new_config[k])
            else:
                old_config[k] = new_config[k]
    return old_config

try:
    import config_override
    configs = revise(configs,config_override.configs)
except ImportError:
    pass

