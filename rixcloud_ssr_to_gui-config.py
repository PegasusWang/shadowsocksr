#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解析从 rixcloud 获取的 ssr api，并导出成 gui-config.json
"""

import base64
import json
import os

import requests


ENV_KEY = 'RIXCLOUD_SSR_API_URL'


def _fill_missing(string):
    # https://github.com/tyong920/ssr_url_parser/blob/master/ssr_url_parser/utils.py
    """Fill base64 decoded string with ="""
    missing_padding = 4 - len(string) % 4
    if missing_padding:
        return string + '=' * missing_padding
    return string


def _b64_url_decode(b64_str):
    return base64.urlsafe_b64decode(_fill_missing(b64_str)).decode()


def parsed_ssr_url(url):
    """
    url: "ssr://"
    """
    ssr_url = url[6:]  # remove prefix 'ssr://'
    parsed_url = base64.urlsafe_b64decode(_fill_missing(ssr_url)).decode()
    url_info, params_str = parsed_url.split('/?')
    config_dict = {}
    server, server_port, protocol, method, obfs, password_b64 = url_info.split(':')
    config_dict = {
        "server": server,
        "serve_port": server_port,
        "protocol": protocol,
        "method": method,
        "obfs": obfs,
        "password": _b64_url_decode(password_b64),
        "enable": True,
    }
    obfs_params = {}
    for pair in params_str.split('&'):
        k, v = pair.split('=')
        obfs_params[k] = _b64_url_decode(v)
    config_dict.update(obfs_params)
    return config_dict


def parse_text_ssr(text):
    """rixcloud 端口复用配置"""
    urls = [i for i in text.split() if i]
    configs = []
    for url in urls:
        config_dict = parsed_ssr_url(url)
        configs.append(config_dict)
    return configs


def parse():
    # url = os.getenv(ENV_KEY)
    # import ipdb;ipdb.set_trace()
    # if url is None:
    rixcloud_path = os.path.expanduser("~/.rixcloud")
    url = open(rixcloud_path).read()
    assert url, 'must set rixcloud ssr url in env, export {}=""'.format(ENV_KEY)
    resp = requests.get(url.strip())
    text = resp.text
    urls = base64.b64decode(text).decode().split('\n')
    urls = [_ for _ in urls if _]
    configs = []
    for url in urls:
        config_dict = parsed_ssr_url(url)
        configs.append(config_dict)
    return configs


def write_gui_config():
    res = {}
    configs = parse()
    res['configs'] = configs
    with open('gui-config.json', 'w') as f:
        json.dump(res, f, indent=4, ensure_ascii=False)


def write_gui_config_ssr_common():
    """端口复用配置写入"""
    with open('_ssr.txt') as f:
        text = f.read().strip()
    res = {}
    configs = parse_text_ssr(text)
    res['configs'] = configs
    with open('gui-config.json', 'w') as f:
        json.dump(res, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # write_gui_config_ssr_common()
    write_gui_config()
