# XSS 过滤
import validators
from markupsafe import escape
from validators import validator


def str_escape(s):
    """
    对字符串进行 XSS 过滤，返回转义后的安全字符串。

    :param s: 需要转义的字符串。
    :return: 返回转义后的字符串，如果输入为空则返回 None。
    """
    if not s:
        return None
    return str(escape(s))


def between(*args, **kwargs):
    """
    验证数字是否介于最小值和最大值之间。
    适用于整数、浮点数、小数和日期等类型。

    :param value: 需要验证的数字。
    :param min: 数字的最小值（可选）。
    :param max: 数字的最大值（可选）。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> between(5, min=2)
        True

        >>> between(13.2, min=13, max=14)
        True

        >>> between(500, max=400)
        ValidationFailure(func=between, args=...)
    """
    return validators.between(*args, **kwargs)


def domain(*args, **kwargs):
    """
    验证给定值是否为有效的域名。

    :param value: 需要验证的域名字符串。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> domain('example.com')
        True

        >>> domain('example.com/')
        ValidationFailure(func=domain, ...)
    """
    return validators.domain(*args, **kwargs)


def email(*args, **kwargs):
    """
    验证给定值是否为有效的电子邮件地址。

    :param value: 需要验证的电子邮件地址。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> email('someone@example.com')
        True

        >>> email('bogus@@')
        ValidationFailure(func=email, ...)
    """
    return validators.email(*args, **kwargs)


def iban(*args, **kwargs):
    """
    验证给定值是否为有效的 IBAN 代码。

    :param value: 需要验证的 IBAN 代码。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> iban('DE29100500001061045672')
        True

        >>> iban('123456')
        ValidationFailure(func=iban, ...)
    """
    return validators.iban(*args, **kwargs)


def ipv4(*args, **kwargs):
    """
    验证给定值是否为有效的 IPv4 地址。

    :param value: 需要验证的 IPv4 地址。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> ipv4('123.0.0.7')
        True

        >>> ipv4('900.80.70.11')
        ValidationFailure(func=ipv4, args={'value': '900.80.70.11'})
    """
    return validators.ipv4(*args, **kwargs)


def ipv6(*args, **kwargs):
    """
    验证给定值是否为有效的 IPv6 地址。

    :param value: 需要验证的 IPv6 地址。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> ipv6('abcd:ef::42:1')
        True

        >>> ipv6('abc.0.0.1')
        ValidationFailure(func=ipv6, args={'value': 'abc.0.0.1'})
    """
    return validators.ipv6(*args, **kwargs)


def length(*args, **kwargs):
    """
    验证给定字符串的长度是否在指定范围内。

    :param value: 需要验证的字符串。
    :param min: 字符串的最小长度（可选）。
    :param max: 字符串的最大长度（可选）。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> length('something', min=2)
        True

        >>> length('something', min=9, max=9)
        True

        >>> length('something', max=5)
        ValidationFailure(func=length, ...)
    """
    return validators.length(*args, **kwargs)


def mac_address(*args, **kwargs):
    """
    验证给定值是否为有效的 MAC 地址。

    :param value: 需要验证的 MAC 地址。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> mac_address('01:23:45:67:ab:CD')
        True

        >>> mac_address('00:00:00:00:00')
        ValidationFailure(func=mac_address, args={'value': '00:00:00:00:00'})
    """
    return validators.mac_address(*args, **kwargs)


def slug(*args, **kwargs):
    """
    验证给定值是否为有效的 Slug 格式。
    有效的 Slug 只能包含字母数字字符、连字符和下划线。

    :param value: 需要验证的字符串。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> slug('my.slug')
        ValidationFailure(func=slug, args={'value': 'my.slug'})

        >>> slug('my-slug-2134')
        True
    """
    return validators.slug(*args, **kwargs)


def url(*args, **kwargs):
    """
    验证给定值是否为有效的 URL。

    :param value: 需要验证的 URL。
    :param public: 是否仅允许公共 URL（可选）。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> url('http://foobar.dk')
        True

        >>> url('http://10.0.0.1')
        True

        >>> url('http://foobar.d')
        ValidationFailure(func=url, ...)

        >>> url('http://10.0.0.1', public=True)
        ValidationFailure(func=url, ...)
    """
    return validators.url(*args, **kwargs)


def uuid(*args, **kwargs):
    """
    验证给定值是否为有效的 UUID。

    :param value: 需要验证的 UUID。
    :return: 如果验证成功返回 True，否则返回 ValidationFailure。

    示例：
        >>> uuid('2bc1c94f-0deb-43e9-92a1-4775189ec9f8')
        True

        >>> uuid('2bc1c94f 0deb-43e9-92a1-4775189ec9f8')
        ValidationFailure(func=uuid, ...)
    """
    return validators.uuid(*args, **kwargs)


@validator
def even(value):
    """
    验证给定值是否为偶数。

    :param value: 需要验证的数字。
    :return: 如果是偶数返回 True，否则返回 ValidationFailure。

    示例：
        >>> even(4)
        True

        >>> even(5)
        ValidationFailure(func=even, args={'value': 5})
    """
    return not (value % 2)