#!/usr/bin/python

import os
import sys
import argparse
import pyshark
from pprint import pprint


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'pcap', help='pcap file captured by tcpdump')
    parser.add_argument(
        'cc', metavar='congestion-control',
        help='congestion control scheme that generated the pcap files')
    parser.add_argument(
        'role', choices=['server', 'client'],
        help='server or client')
    parser.add_argument(
        'server_port', metavar='server-port', type=int,
        help='the port that server is listening to')
    parser.add_argument(
        '-i', metavar='INGRESS-LOG', action='store', dest='ingress_log',
        required=True, help='ingress log to save')
    parser.add_argument(
        '-e', metavar='EGRESS-LOG', action='store', dest='egress_log',
        required=True, help='egress log to save')

    return parser.parse_args()


def get_uid(pkt, cc):
    if cc == 'pcc':
        return 0


def main():
    args = parse_arguments()

    receiver_first_schemes = [
        'default_tcp', 'koho_cc', 'ledbat', 'pcc', 'scream', 'sprout', 'vegas']
    sender_first_schemes = ['quic', 'verus', 'webrtc']

    is_receiver_first = args.cc in receiver_first_schemes
    if not is_receiver_first:
        assert args.cc in sender_first_schemes

    ingress_log = open(args.ingress_log, 'w')
    egress_log = open(args.egress_log, 'w')

    is_server = args.role == 'server'
    init_ts = -1
    pcap = pyshark.FileCapture(os.path.abspath(args.pcap))
    for pkt in pcap:
        ts = int(round(float(pkt.sniff_timestamp) * 1000))
        if init_ts == -1:
            init_ts = ts
            ingress_log.write('# ingress: %s\n' % init_ts)
            egress_log.write('# egress: %s\n' % init_ts)

        ts -= init_ts
        size = int(pkt.ip.len)

        src_port = int(pkt.udp.srcport)
        dst_port = int(pkt.udp.dstport)

        is_destined_for_server = dst_port == args.server_port
        if not is_destined_for_server:
            assert src_port == args.server_port

        uid = get_uid(pkt, args.cc)
        line = '%s - %s - %s\n' % (ts, uid, size)

        if is_server == is_destined_for_server:
            ingress_log.write(line)
        else:
            egress_log.write(line)

    ingress_log.close()
    egress_log.close()


if __name__ == '__main__':
    main()
