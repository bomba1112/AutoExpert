"""Build the existing Android WebView shell using an installed SDK/JDK on Windows or Unix."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]


def main() -> None:
    sdk = Path(
        os.environ.get("ANDROID_SDK_ROOT")
        or os.environ.get("ANDROID_HOME")
        or Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk"
    )
    jdk = Path(os.environ.get("JAVA_HOME") or "C:/Program Files/Android/Android Studio/jbr")
    version = os.environ.get("ANDROID_BUILD_TOOLS_VERSION", "35.0.0")
    platform = os.environ.get("ANDROID_COMPILE_SDK", "35")
    tools = sdk / "build-tools" / version
    android_jar = sdk / "platforms" / f"android-{platform}" / "android.jar"
    suffix = ".exe" if os.name == "nt" else ""
    java, javac, keytool = [jdk / "bin" / (name + suffix) for name in ("java", "javac", "keytool")]
    aapt, zipalign = [tools / (name + suffix) for name in ("aapt2", "zipalign")]
    for required in (
        java,
        javac,
        keytool,
        aapt,
        zipalign,
        android_jar,
        tools / "lib/d8.jar",
        tools / "lib/apksigner.jar",
    ):
        if not required.is_file():
            raise SystemExit(f"Missing build dependency: {required}")
    manifest = ET.parse(PROJECT / "AndroidManifest.xml").getroot()
    version_name = manifest.attrib["{http://schemas.android.com/apk/res/android}versionName"]
    version_code = manifest.attrib["{http://schemas.android.com/apk/res/android}versionCode"]
    apk_name = f"AutoExpert_2_0_Alpha_{version_name.removesuffix('-alpha')}.apk"
    output = ROOT / "deliverables" / apk_name
    output.parent.mkdir(exist_ok=True)
    api = os.environ.get("AUTOEXPERT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")
    if not api.startswith(("https://", "http://")):
        raise SystemExit("AUTOEXPERT_API_BASE_URL must be an HTTP(S) URL")
    keystore = Path(
        os.environ.get("AUTOEXPERT_ANDROID_KEYSTORE") or ROOT / ".signing/autoexpert-alpha.jks"
    )
    alias = os.environ.get("AUTOEXPERT_ANDROID_KEY_ALIAS", "autoexpert-alpha")
    environment = dict(os.environ)
    environment.setdefault("AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD", "android-alpha")

    def run(*args: object) -> None:
        subprocess.run([str(arg) for arg in args], check=True, env=environment)

    with tempfile.TemporaryDirectory(prefix="autoexpert-android-") as folder:
        build = Path(folder)
        res = build / "res"
        shutil.copytree(PROJECT / "res", res)
        template = res / "values/runtime.xml.template"
        escaped = api.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        (res / "values/runtime.xml").write_text(
            template.read_text(encoding="utf-8").replace("__API_BASE_URL__", escaped),
            encoding="utf-8",
        )
        template.unlink()
        for directory in ("generated", "classes", "dex"):
            (build / directory).mkdir()
        run(aapt, "compile", "--dir", res, "-o", build / "resources.zip")
        run(
            aapt,
            "link",
            "-o",
            build / "base.apk",
            "-I",
            android_jar,
            "--manifest",
            PROJECT / "AndroidManifest.xml",
            "--java",
            build / "generated",
            "--min-sdk-version",
            "24",
            "--target-sdk-version",
            "35",
            "--version-code",
            version_code,
            "--version-name",
            version_name,
            build / "resources.zip",
        )
        run(
            javac,
            "-encoding",
            "UTF-8",
            "-source",
            "8",
            "-target",
            "8",
            "-classpath",
            android_jar,
            "-d",
            build / "classes",
            PROJECT / "src/com/autoexpert/demo/MainActivity.java",
            build / "generated/com/autoexpert/demo/R.java",
        )
        run(
            java,
            "-cp",
            tools / "lib/d8.jar",
            "com.android.tools.r8.D8",
            "--lib",
            android_jar,
            "--min-api",
            "24",
            "--output",
            build / "dex",
            *sorted((build / "classes").rglob("*.class")),
        )
        with zipfile.ZipFile(build / "base.apk", "a", compression=zipfile.ZIP_DEFLATED) as apk:
            apk.write(build / "dex/classes.dex", "classes.dex")
            assets = ROOT / "apps/web_preview"
            for asset in sorted(assets.rglob("*")):
                if asset.is_file():
                    apk.write(asset, "assets/preview/" + asset.relative_to(assets).as_posix())
        run(zipalign, "-f", "4", build / "base.apk", build / "aligned.apk")
        keystore.parent.mkdir(exist_ok=True, parents=True)
        if not keystore.exists():
            run(
                keytool,
                "-genkeypair",
                "-noprompt",
                "-keystore",
                keystore,
                "-storepass:env",
                "AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD",
                "-keypass:env",
                "AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD",
                "-alias",
                alias,
                "-keyalg",
                "RSA",
                "-keysize",
                "2048",
                "-validity",
                "3650",
                "-dname",
                "CN=Auto Expert Android Alpha,O=Development,C=AZ",
            )
        signer = (java, "-jar", tools / "lib/apksigner.jar")
        run(
            *signer,
            "sign",
            "--ks",
            keystore,
            "--ks-key-alias",
            alias,
            "--ks-pass",
            "env:AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD",
            "--key-pass",
            "env:AUTOEXPERT_ANDROID_KEYSTORE_PASSWORD",
            "--out",
            output,
            build / "aligned.apk",
        )
        run(*signer, "verify", "--verbose", "--print-certs", output)
    print(f"APK: {output}\nAPI: {api}")


if __name__ == "__main__":
    main()
