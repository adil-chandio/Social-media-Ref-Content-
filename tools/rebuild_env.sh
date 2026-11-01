#!/usr/bin/env bash
# Rebuild the headless-Blender stub libs in /tmp/xstub after a sandbox reset.
# Usage: bash tools/rebuild_env.sh [stubs|syms]
set -e
BPY=/tmp/bpyvenv/lib/python3.11/site-packages/bpy
mkdir -p /tmp/xstub
nm -D --undefined-only $BPY/_bpy.so $BPY/*.so $BPY/lib/*.so 2>/dev/null \
  | awk '{print $NF}' | sed 's/@.*//' | sort -u > /tmp/want_all.txt
{ nm -D --defined-only $BPY/lib/*.so 2>/dev/null | awk '{print $NF}'
  nm -D --defined-only /usr/lib/x86_64-linux-gnu/libc.so.6 /usr/lib/x86_64-linux-gnu/libm.so.6 \
    /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/libgcc_s.so.1 2>/dev/null | awk '{print $NF}'
} | sed 's/@.*//' | sort -u > /tmp/have.txt
comm -23 /tmp/want_all.txt /tmp/have.txt | grep -v "^Py" | grep -v "^_Py" > /tmp/stubsyms_all.txt
grep -E "^_?(X[A-Za-z0-9_]*|glX[A-Za-z0-9_]*|gl[A-Z][A-Za-z0-9_]*|vk[A-Z][A-Za-z0-9_]*|Smc[A-Za-z0-9_]*|Ice[A-Za-z0-9_]*|xcb_[a-z0-9_]*|xkb_[a-z0-9_]*|__gmon_start__|_ITM_[a-zA-Z0-9_]*|_Unwind_[A-Za-z0-9_]*)$" \
  /tmp/stubsyms_all.txt | sort -u > /tmp/xstub_syms.txt
{ echo '// auto-generated X/GL/VK/ICE/SM/xkb stubs (headless bpy)'; while read s; do echo "void $s(void){}"; done < /tmp/xstub_syms.txt; } > /tmp/xstub/stub.c
for L in libXrender.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1; do
  gcc -shared -fPIC -o /tmp/xstub/$L /tmp/xstub/stub.c
done
printf 'V_0.5.0 { global: *; };\n' > /tmp/xstub/ver.map
gcc -shared -fPIC -o /tmp/xstub/libxkbcommon.so.0 /tmp/xstub/stub.c -Wl,--version-script=/tmp/xstub/ver.map
echo "stubs ready: $(ls /tmp/xstub | tr '\n' ' ')"
