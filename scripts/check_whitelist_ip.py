#!/usr/bin/env python3
"""Проверка IP по мобильным белым спискам hxehex/russia-mobile-internet-whitelist.

Использование:
    python3 scripts/check_whitelist_ip.py <IP> [<IP> ...]
    WL_DIR=./wl python3 scripts/check_whitelist_ip.py 51.250.1.2   # взять списки из локальной папки

Файлы репозитория (формат с 09.2026):
    cidrwhitelist.txt — подсети в CIDR (например 2.63.0.0/17);
    ipwhitelist.txt   — отдельные IP, по одному на строку (раньше это был cidrwhitelist.txt).

Списки собраны сообществом с разных операторов и регионов. Попадание в список —
повод проверить IP с SIM нужного оператора во время БС, а не гарантия.
"""
import ipaddress
import os
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/"
FILES = ("cidrwhitelist.txt", "ipwhitelist.txt")


def load(name):
    wl_dir = os.environ.get("WL_DIR")
    if wl_dir:
        with open(os.path.join(wl_dir, name), encoding="utf-8") as f:
            return f.read().splitlines()
    with urllib.request.urlopen(BASE + name, timeout=60) as r:
        return r.read().decode("utf-8", "replace").splitlines()


def main(args):
    if not args:
        print(__doc__.strip())
        return 2
    targets = [ipaddress.ip_address(a) for a in args]
    nets, ips = [], set()
    for name in FILES:
        for line in load(name):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                if "/" in line:
                    nets.append(ipaddress.ip_network(line, strict=False))
                else:
                    ips.add(ipaddress.ip_address(line))
            except ValueError:
                continue
    for ip in targets:
        hits = [str(n) for n in nets if ip.version == n.version and ip in n]
        if ip in ips:
            hits.append("точный IP в ipwhitelist.txt")
        net24 = ipaddress.ip_network(f"{ip}/24", strict=False) if ip.version == 4 else None
        same24 = sum(1 for x in ips if net24 and x.version == 4 and x in net24)
        status = "В СПИСКЕ" if hits else "нет"
        print(f"{ip}: {status}" + (f" ({', '.join(hits[:5])})" if hits else ""),
              f"| соседей по /24 в ipwhitelist: {same24}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
