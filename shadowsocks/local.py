#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import, division, print_function, \
    with_statement

import sys
import os
import logging
import signal

if __name__ == '__main__':
    import inspect
    file_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
    sys.path.insert(0, os.path.join(file_path, '../'))

from shadowsocks import shell, daemon, eventloop, tcprelay, udprelay, asyncdns, common


def run(config, loop):
    shell.check_python()

    # fix py2exe
    if hasattr(sys, "frozen") and sys.frozen in \
            ("windows_exe", "console_exe"):
        p = os.path.dirname(os.path.abspath(sys.executable))
        os.chdir(p)

    if not config.get('dns_ipv6', False):
        asyncdns.IPV6_CONNECTION_SUPPORT = False

    daemon.daemon_exec(config)
    logging.info("local start with protocol[%s] password [%s] method [%s] obfs [%s] obfs_param [%s] server [%s]" % (
        config['protocol'], '**', config['method'], config['obfs'], config.get('obfs_param'), config['server']))

    logging.info("starting local at %s:%d" %
                 (config['local_address'], config['local_port']))

    dns_resolver = asyncdns.DNSResolver()
    tcp_server = tcprelay.TCPRelay(config, dns_resolver, True)
    udp_server = udprelay.UDPRelay(config, dns_resolver, True)
    dns_resolver.add_to_loop(loop)
    tcp_server.add_to_loop(loop)
    udp_server.add_to_loop(loop)

    def handler(signum, _):
        logging.warn('received SIGQUIT, doing graceful shutting down..')
        tcp_server.close(next_tick=True)
        udp_server.close(next_tick=True)
    signal.signal(getattr(signal, 'SIGQUIT', signal.SIGTERM), handler)

    def int_handler(signum, _):
        sys.exit(1)
    signal.signal(signal.SIGINT, int_handler)

    daemon.set_user(config.get('user', None))
    loop.run()


REGION_MAP = {
    'us': u'美国',
    'jp': u'日本',
    'hk': u'香港',
}


def load_gui_json_config(region, configfile_name='gui-config.json'):
    """解析直接从 rixcloud 下载的配置文件"""
    import json
    import random
    config_path = shell.find_config('config.json')
    gui_config_path = shell.find_config(configfile_name)
    region_cn = REGION_MAP[region]
    with open(gui_config_path) as f:
        gui_config = json.load(f)
        configs = gui_config['configs']
        configs = [c for c in configs if region_cn in c['remarks']]
        random_config = random.choice(configs)
        del random_config['remarks']    # 删除中文的字段
        # overwrite origin config.json
        with open(config_path, 'w') as _f:
            json.dump(random_config, _f ,indent=4)
        random_config['local_address'] = '127.0.0.1'
        random_config['local_port'] = 1080
        random_config['obfsparam'] = common.to_bytes(random_config.pop('obfsparam'))
        random_config['server_port'] = int(random_config.pop('serve_port'))
        return random_config


def main(use_rix_config=1):
    import time
    try:
        region = sys.argv[1]
    except IndexError:
        region = 'us'
    while True:
        try:
            loop = eventloop.EventLoop()
            if use_rix_config:
                rix_config = load_gui_json_config(common.to_unicode(region))
                config = shell.get_config(True)
                config.update(rix_config)
                config['password'] = common.to_bytes(rix_config['password'])
                config['server'] = str(rix_config['server'])
                config['verbose'] = 1
                config['timeout'] = 120
                config['connect_verbose_info'] = 1
            else:
                config = shell.get_config(True)
            import pprint; pprint.pprint(config)
            run(config, loop)
        except Exception as e:
            import traceback
            traceback.print_exc()
            loop.stop()
            time.sleep(1)
            print('restart.................')
        except KeyboardInterrupt as e:
            shell.print_exception(e)
            sys.exit(1)
            print('exit....................')


if __name__ == '__main__':
    main()
