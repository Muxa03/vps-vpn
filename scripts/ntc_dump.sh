#!/usr/bin/env bash
# Выгрузка ключевых тем ntc.party через открытый API Discourse.
# Запускать в корне репозитория vps-vpn на своей машине (из РФ — с включённым VPN).
set -u
OUT=ntc-dump; mkdir -p "$OUT/search"
IDS="22516 17013 22934 16061 7318 24074 22222 20591 25528 24845 23653 21989 22139 20340
24119 14369 13523 23589 19123 21884 24230 24735 23468 19553 24403 23943 17148 18258
20253 13366 14695 18319 11841 8850 11881 8203 12845 16852 22319 13380 18135 22292
21459 13855 23924 23843 23690 24031 23842 24093"
for id in $IDS; do
  prev=""
  for p in $(seq 1 30); do
    f="$OUT/$id.p$p.md"
    curl -sfL -A "Mozilla/5.0" "https://ntc.party/raw/$id?page=$p" -o "$f" || { rm -f "$f"; break; }
    h=$(md5sum < "$f" | cut -d' ' -f1)
    if [ "$(wc -c < "$f")" -lt 50 ] || [ "$h" = "$prev" ]; then rm -f "$f"; break; fi
    prev=$h; echo "ok $id p$p"; sleep 1
  done
done
for q in "хостинг vps after:2026-01-01" "мегафон reality after:2026-06-01" "релей яндекс облако" \
         "fingerprint firefox after:2026-05-01" "xhttp мобильный after:2026-06-01" "белые списки релей after:2026-07-01"; do
  curl -sfL -A "Mozilla/5.0" -G "https://ntc.party/search.json" --data-urlencode "q=$q" \
    -o "$OUT/search/$(echo "$q" | tr ' :/' '___').json" && echo "ok search: $q"; sleep 1
done
du -sh "$OUT"
