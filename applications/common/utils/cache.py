import time

cache_dict = {}


def cache_set_internal(key, value, expired=5):
    """
    程序内部实现的记录缓存，用于简单、体量不大的缓存记录，在程序结束后销毁。对于高速、体量大的环境请配置 Redis 等服务自行记录。
    记录缓存，存储键值对，并记录当前时间作为缓存的时间戳。

    :param key: 键
    :param value: 值
    :param expired: 过期时间（秒），默认5秒
    """
    cache_dict[key] = {
        'value': value,
        'expired_time': time.time() + expired
    }


def cache_get_internal(key):
    """
    获取缓存，根据键从缓存中获取值，并检查是否过期。

    :param key: 键
    :return: 如果缓存存在且未过期，返回缓存的值；否则返回 None
    """
    if key in cache_dict:
        cache_item = cache_dict[key]
        if time.time() < cache_item['expired_time']:
            return cache_item['value']
        else:
            # 如果缓存已过期，删除该缓存
            del cache_dict[key]
    return None


def cache_auto_internal(key, call, expired=5):
    """
    如果缓存存在直接返回缓存内容，缓存不存在或者过期执行 call 函数，并取得返回值记录并返回。

    :param key: 键
    :param call: 获取新值的地方
    :param expired: 过期时间（秒），默认5秒
    """

    data = cache_get_internal(key)

    if data is not None:
        return data

    data = call()
    cache_set_internal(key, data, expired)

    return data
