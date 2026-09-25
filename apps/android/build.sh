#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "$0")" && pwd)
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-21-openjdk-amd64}"
gradle_bin=""
if [[ -n "${GRADLE_HOME:-}" ]]; then
    gradle_bin="$GRADLE_HOME/bin/gradle"
else
    for candidate in "${GRADLE_USER_HOME:-$HOME/.gradle}"/wrapper/dists/gradle-8.14.3-all/*/gradle-8.14.3/bin/gradle; do
        if [[ -x "$candidate" ]]; then gradle_bin="$candidate"; break; fi
    done
fi
if [[ ! -x "$gradle_bin" || ! -x "$JAVA_HOME/bin/javac" ]]; then
    printf '%s\n' 'Set GRADLE_HOME and JAVA_HOME to existing Gradle 8.14.3 and JDK installations.' >&2
    exit 1
fi
# No toolchain download or overlapping LazyPromotion build.
exec 9>"$project_dir/.build.lock"
flock -n 9 || { printf '%s\n' 'A LazyPromotion Android build is already running.' >&2; exit 1; }
exec "$gradle_bin" -p "$project_dir" --offline --no-daemon --max-workers=2 "$@"
