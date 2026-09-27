#!/usr/bin/env bash
# Выгрузка ключевых тем ntc.party через открытый API Discourse.
# Запуск: ./scripts/ntc_dump.sh [id ...]   (без аргументов — список по умолчанию)
# NTC_BASE=https://ntc.rkn.quest ./scripts/ntc_dump.sh   — если ntc.party недоступен (из РФ без VPN).
# У больших тем (>300 постов) качаются только последние 3 страницы по 100 постов — там актуальное.
set -u
BASE="${NTC_BASE:-https://ntc.party}"
OUT="${NTC_OUT:-ntc-dump}"; mkdir -p "$OUT/search"
IDS="${*:-26076 25993 25528 25362 25610 25306 25816 16061 17013 22516 22237 12845 22934 24845 23653
20253 13366 4867 22292 22319 25179 25295 14695 18319 11841 8850 11881
24230 24735 16325 23018 21884 24402 23943 24119 17148 18258
23690 24753 24955 24031 25449 13855 23843 21459 23924}"

get() { curl -sfL -m 30 -A "Mozilla/5.0" "$@"; }

for id in $IDS; do
  n=$(get "$BASE/t/$id.json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("posts_count",0))' 2>/dev/null || echo 0)
  [ "$n" -gt 0 ] || { echo "skip $id (нет доступа)"; continue; }
  pages=$(( (n + 99) / 100 )); first=1; [ "$n" -gt 300 ] && first=$(( pages - 2 ))
  f="$OUT/$id.md"; : > "$f"
  for p in $(seq "$first" "$pages"); do
    printf '\n\n===== %s page %s =====\n' "$id" "$p" >> "$f"
    get "$BASE/raw/$id?page=$p" >> "$f"; sleep 1
  done
  echo "ok $id ($n постов, страницы $first..$pages)"; sleep 1
done

for q in "хостинг after:2026-06-01" "хостер after:2026-06-01" "релей after:2026-06-01" "каскад after:2026-06-01" \
         "мегафон after:2026-06-01" "fingerprint after:2026-06-01" "xhttp after:2026-06-01" "белые списки after:2026-07-01" \
         "16кб after:2026-07-01" "блокировка ip after:2026-08-01"; do
  get -G "$BASE/search.json" --data-urlencode "q=$q" -o "$OUT/search/$(echo "$q" | tr ' :/' '___').json" && echo "ok search: $q"
  sleep 1
done
du -sh "$OUT"
