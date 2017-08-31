#! /usr/bin/python
# coding: utf8

import configparser
import argparse
import json


url_prefix = 'http://'
url_suffix = ':8091/status/format/json'

def read_inv(_file):
    try:
        inv_confparser = configparser.RawConfigParser(allow_no_value=True)
        inv_confparser.read(_file)
    except Exception as e:
        print('[ERROR]: Error parse inv file.\nERROR: {0}'.format(e))
        exit(1)
    return inv_confparser

def inv_collect_data(_file):
    inv_confparser = read_inv(_file)

    res = {}
    for section in inv_confparser.sections():
        if ':' in section:
            continue

        item = '='.join(inv_confparser.items(section)[0])

        ip = ''
        for item in  item.split(' '):
            item = item.split('=')
            if item[0]=='ansible_host':
                ip = item[1]

        if ip == '':
            print('[ERROR]: ip not found in section={}'.format(section))
            exit(1)

        res.update({ section.upper(): '{}{}{}'.format(url_prefix, ip, url_suffix) })

    return res

def read_conf(_file):
    try:
        with open(_file) as json_data:
            conf_json = json.load(json_data)
    except Exception as e:
        print('[ERROR]: Error read conf file.\nERROR: {0}'.format(e))
        return []
    return conf_json

def conf_collect_data(_file):
    conf_data = read_conf(_file)

    res = {}
    for item in conf_data.get('nginxScrapeURIs', []):
        res.update({ item.get('hostName', ''): item.get('uri', '') })

    return res

def compare_data(inv_data, conf_data):
    for_add_keys = set.difference(set(inv_data.keys()), set(conf_data.keys()))
    for_del_keys = set.difference(set(conf_data.keys()), set(inv_data.keys()))
    for_stay_keys = set.intersection(set(conf_data.keys()), set(inv_data.keys()))

    for_add = []
    for item in for_add_keys:
        for_add.append({ 'hostName': item.upper(), 'uri': inv_data[item]  })

    for_del = [i for i in for_del_keys if '-' not in i]

    for_stay = []
    for item in for_stay_keys:
        if inv_data[item]==conf_data[item]:
            for_stay.append(item)
            continue
        for_del.append(item)
        for_add.append({ 'hostName': item.upper(), 'uri': inv_data[item] })



    return for_add, for_del, for_stay

def arg_parse():
    parser = argparse.ArgumentParser(description='Util for find difference in ansble inv file and nginx-vts-exporter config')


    parser.add_argument('--inv', dest='inv', type=str, required=True)
    parser.add_argument('--conf', dest='conf', type=str, required=True)

    args = parser.parse_args()

    return args

def main():
    args = arg_parse()
    inv_data = inv_collect_data(args.inv)
    conf_data = conf_collect_data(args.conf)
    for_add, for_del, for_stay = compare_data(inv_data, conf_data)

    print('FOR DELETE: {}'.format(json.dumps(for_del, indent=2)))
    print('')
    print('FOR ADD: {}'.format(json.dumps(for_add, indent=2)))
    print('')
    print('FOR STAY: {}'.format(json.dumps(for_stay, indent=2)))

if __name__ == '__main__':
    main()
