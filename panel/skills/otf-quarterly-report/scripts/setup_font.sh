#!/usr/bin/env bash
# Lato 是全篇字体。新容器通常没装，装完必须清 matplotlib 字体缓存，
# 否则会静默 fallback 成 DejaVu，整套图的字形就走形了。
set -e
if ! fc-list | grep -qi lato; then
  apt-get install -y fonts-lato
fi
rm -rf ~/.cache/matplotlib
python3 - <<'PY'
import matplotlib, matplotlib.font_manager as fm
names = sorted({f.name for f in fm.fontManager.ttflist})
print('Lato installed:', 'Lato' in names)
PY
