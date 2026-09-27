#!/usr/bin/env python3
"""Какая доля адресов хостера попадает в мобильный белый список (hxehex).

Использование:
    python3 scripts/whitelist_by_asn.py                     # набор российских облаков по умолчанию
    python3 scripts/whitelist_by_asn.py AS200350 AS49505    # свои ASN
    WL_DIR=./wl python3 scripts/whitelist_by_asn.py         # списки из локальной папки

Префиксы ASN берутся из RIPEstat (announced-prefixes), белые подсети — из
cidrwhitelist.txt репозитория hxehex/russia-mobile-internet-whitelist.
Для каждого ASN печатается: всего IPv4, сколько из них в белых подсетях, и по /16
«белых /24 из всех /24» — это подсказка, из какого диапазона выбивать IP.

Оговорки: список общий для всех операторов и регионов и отстаёт (например,
158.160.x Yandex Cloud в нём ещё есть, хотя на форуме пишут, что пул выбыл
в 05.2026, а у T2 диапазонов YC нет). Итог проверяй с SIM нужного оператора во время БС.
"""
import collections
import ipaddress
import json
import os
import sys
import time
import urllib.request

WL_URL = "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/cidrwhitelist.txt"
RIPE = "https://stat.ripe.net/data/announced-prefixes/data.json?resource={}"

DEFAULT = {
    "AS200350": "Yandex Cloud", "AS47764": "VK Cloud (VK)", "AS49505": "Selectel",
    "AS50340": "Selectel MSK", "AS9123": "Timeweb", "AS198610": "Beget",
    "AS208677": "Cloud.ru", "AS197695": "REG.RU", "AS29182": "FirstVDS (JSC IOT)",
    "AS210756": "EdgeCenter", "AS44112": "SpaceWeb", "AS35278": "Sprinthost",
}


def load_wl():
    wl_dir = os.environ.get("WL_DIR")
    if wl_dir:
        with open(os.path.join(wl_dir, "cidrwhitelist.txt"), encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        with urllib.request.urlopen(WL_URL, timeout=60) as r:
            lines = r.read().decode("utf-8", "replace").splitlines()
    nets = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and ":" not in line:
            try:
                nets.append(ipaddress.ip_network(line, strict=False))
            except ValueError:
                pass
    return nets


def merge(nets):
    iv = sorted((int(n.network_address), int(n.broadcast_address)) for n in nets)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def covered(a, b, wl):
    """Сколько адресов из [a, b] лежит в объединённых белых интервалах wl."""
    total = 0
    for x, y in wl:
        if y < a:
            continue
        if x > b:
            break
        total += min(b, y) - max(a, x) + 1
    return total


def main(args):
    asns = {a.upper(): DEFAULT.get(a.upper(), "") for a in args} if args else DEFAULT
    wl = merge(load_wl())
    for asn, name in asns.items():
        try:
            with urllib.request.urlopen(RIPE.format(asn), timeout=60) as r:
                data = json.load(r)
        except Exception as e:  # noqa: BLE001 — печатаем и идём дальше
            print(f"{asn}: ошибка RIPEstat: {e}")
            continue
        prefixes = [ipaddress.ip_network(p["prefix"]) for p in data["data"]["prefixes"] if ":" not in p["prefix"]]
        blocks = merge(prefixes)
        total = sum(b - a + 1 for a, b in blocks)
        white = sum(covered(a, b, wl) for a, b in blocks)
        per16_all, per16_white = collections.Counter(), collections.Counter()
        for a, b in blocks:
            for start in range(a - a % 256, b + 1, 256):
                key = str(ipaddress.ip_address(start)).rsplit(".", 2)[0]
                per16_all[key] += 1
                if covered(start, start + 255, wl) > 0:
                    per16_white[key] += 1
        pct = 100 * white / total if total else 0
        print(f"\n{asn} {name}: IPv4 {total}, в белых подсетях {white} ({pct:.1f}%)")
        top = sorted(per16_all, key=lambda k: (-per16_white[k], -per16_all[k]))[:12]
        print("  " + "  ".join(f"{k}.x {per16_white[k]}/{per16_all[k]}" for k in top))
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
