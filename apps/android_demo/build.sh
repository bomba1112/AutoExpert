#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$project_dir/../.." && pwd)"
sdk_root="${ANDROID_SDK_ROOT:-$repo_root/.tooling/android-sdk}"
build_tools_version="${ANDROID_BUILD_TOOLS_VERSION:-35.0.0}"
api_level="${ANDROID_COMPILE_SDK:-35}"
api_base_url="${AUTOEXPERT_API_BASE_URL:-http://127.0.0.1:8000/api/v1}"
version_name="${AUTOEXPERT_ANDROID_VERSION_NAME:-0.6.7-alpha}"
version_code="${AUTOEXPERT_ANDROID_VERSION_CODE:-66}"
output_apk="${1:-$repo_root/deliverables/AutoExpert_2_0_Alpha_0.6.7.apk}"

case "$api_base_url" in
  http://*|https://*) ;;
  *) echo "AUTOEXPERT_API_BASE_URL must be an absolute HTTP(S) URL" >&2; exit 2 ;;
esac

tools_dir="$sdk_root/build-tools/$build_tools_version"
android_jar="$sdk_root/platforms/android-$api_level/android.jar"
for required in "$tools_dir/aapt2" "$tools_dir/d8" "$tools_dir/zipalign" \
  "$tools_dir/apksigner" "$android_jar"; do
  if [[ ! -e "$required" ]]; then
    echo "Missing Android build dependency: $required" >&2
    exit 3
  fi
done

build_dir="$project_dir/build"
if [[ "$build_dir" != "$project_dir/build" ]]; then
  echo "Unsafe build directory" >&2
  exit 4
fi
rm -rf "$build_dir"
mkdir -p "$build_dir/res" "$build_dir/generated" "$build_dir/classes" \
  "$build_dir/dex" "$build_dir/package/assets/preview" "$(dirname "$output_apk")"

cp -R "$project_dir/res/." "$build_dir/res/"
api_xml_value="${api_base_url//&/&amp;}"
api_xml_value="${api_xml_value//</&lt;}"
api_xml_value="${api_xml_value//>/&gt;}"
sed "s|__API_BASE_URL__|$api_xml_value|g" \
  "$project_dir/res/values/runtime.xml.template" \
  > "$build_dir/res/values/runtime.xml"
rm "$build_dir/res/values/runtime.xml.template"

"$tools_dir/aapt2" compile --dir "$build_dir/res" -o "$build_dir/resources.zip"
"$tools_dir/aapt2" link \
  -o "$build_dir/base.apk" \
  -I "$android_jar" \
  --manifest "$project_dir/AndroidManifest.xml" \
  --java "$build_dir/generated" \
  --min-sdk-version 24 \
  --target-sdk-version 35 \
  --version-code "$version_code" \
  --version-name "$version_name" \
  "$build_dir/resources.zip"

if command -v javac >/dev/null 2>&1; then
  javac_command=(javac)
else
  javac_command=(java --module jdk.compiler/com.sun.tools.javac.Main)
fi
"${javac_command[@]}" -encoding UTF-8 -source 8 -target 8 \
  -classpath "$android_jar" \
  -d "$build_dir/classes" \
  "$project_dir/src/com/autoexpert/demo/MainActivity.java" \
  "$build_dir/generated/com/autoexpert/demo/R.java"

mapfile -t class_files < <(find "$build_dir/classes" -type f -name '*.class' | sort)
"$tools_dir/d8" --lib "$android_jar" --min-api 24 --output "$build_dir/dex" \
  "${class_files[@]}"

cp -R "$repo_root/apps/web_preview/." "$build_dir/package/assets/preview/"
cp "$build_dir/base.apk" "$build_dir/unaligned.apk"
(
  cd "$build_dir/dex"
  zip -q -j "$build_dir/unaligned.apk" classes.dex
)
(
  cd "$build_dir/package"
  zip -q -r "$build_dir/unaligned.apk" assets
)

"$tools_dir/zipalign" -f 4 "$build_dir/unaligned.apk" "$build_dir/aligned.apk"

signing_dir="$repo_root/.signing"
keystore="${AUTOEXPERT_ANDROID_KEYSTORE:-$signing_dir/autoexpert-alpha.jks}"
store_password="${AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD:-android-alpha}"
key_alias="${AUTOEXPERT_ANDROID_KEY_ALIAS:-autoexpert-alpha}"
mkdir -p "$(dirname "$keystore")"
if [[ ! -f "$keystore" ]]; then
  keytool -genkeypair -noprompt \
    -keystore "$keystore" \
    -storepass "$store_password" \
    -keypass "$store_password" \
    -alias "$key_alias" \
    -keyalg RSA \
    -keysize 2048 \
    -validity 3650 \
    -dname "CN=Auto Expert Android Alpha,O=Development,C=AZ"
fi

"$tools_dir/apksigner" sign \
  --ks "$keystore" \
  --ks-key-alias "$key_alias" \
  --ks-pass "pass:$store_password" \
  --key-pass "pass:$store_password" \
  --out "$output_apk" \
  "$build_dir/aligned.apk"

"$tools_dir/apksigner" verify --verbose --print-certs "$output_apk"
printf 'APK: %s\nAPI: %s\n' "$output_apk" "$api_base_url"
