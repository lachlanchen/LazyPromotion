#!/usr/bin/env python3
"""Finite UI check on the already-started, project-owned Android emulator."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "art.lazying.promotion.preview"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial", default="emulator-5590")
    args = parser.parse_args()
    if not re.fullmatch(r"emulator-\d+", args.serial):
        raise SystemExit("Physical devices are outside this check.")

    def adb(*parts, binary=False):
        return subprocess.run([args.adb, "-s", args.serial, *parts], check=True,
                              capture_output=True, text=not binary, timeout=30).stdout

    name = adb("emu", "avd", "name").splitlines()[0].strip()
    if name != "LazyPromotion_Review_API34":
        raise SystemExit("Refusing a different project's emulator.")
    if adb("shell", "getprop", "sys.boot_completed").strip() != "1":
        raise SystemExit("The owned emulator is not ready; no install attempted.")
    evidence = ROOT / ".local/evidence/native-preview-20260926"
    evidence.mkdir(parents=True, exist_ok=True)
    apk = ROOT / "apps/android/app/build/outputs/apk/debug/app-debug.apk"
    adb("install", "-r", str(apk))
    adb("shell", "am", "start", "-W", "-n", f"{PACKAGE}/.MainActivity")

    def tree():
        adb("shell", "uiautomator", "dump", "/sdcard/lazypromotion-preview.xml")
        return ET.fromstring(adb("shell", "cat", "/sdcard/lazypromotion-preview.xml"))

    def node(label):
        for item in tree().iter("node"):
            if item.get("text") != label:
                continue
            bounds = re.findall(r"\d+", item.get("bounds", ""))
            if len(bounds) == 4:
                x1, y1, x2, y2 = map(int, bounds)
                # LazyColumn exposes clipped text nodes at the viewport edge.
                # A four-pixel strip is not a usable visible action or proof.
                if x2 - x1 >= 24 and y2 - y1 >= 24:
                    return item
        return None

    def tap(label):
        item = node(label)
        if item is None:
            raise AssertionError(f"Missing observed control: {label}")
        x1, y1, x2, y2 = map(int, re.findall(r"\d+", item.attrib["bounds"]))
        adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))

    def capture(name):
        # Dump first: UIAutomator waits for idle. Capturing immediately after a
        # tap can record the preceding compositor frame rather than the new UI.
        (evidence / f"{name}.xml").write_text(ET.tostring(tree(), encoding="unicode"))
        (evidence / f"{name}.png").write_bytes(adb("exec-out", "screencap", "-p", binary=True))

    def scroll_to(label):
        for _ in range(6):
            if node(label) is not None:
                return
            dimensions = re.search(r"(\d+)x(\d+)", adb("shell", "wm", "size"))
            width, height = map(int, dimensions.groups())
            adb("shell", "input", "swipe", str(width // 2), str(height * 4 // 5),
                str(width // 2), str(height // 3), "350")
        raise AssertionError(f"Control not found after bounded scroll: {label}")

    try:
        for _ in range(8):
            if node("Products") is not None:
                break
            time.sleep(0.5)
        assert node("L & N: Speech Practice") is not None
        assert node("Bunko: Classics with Ruby") is not None
        capture("android-products")
        tap("Bunko: Classics with Ruby")
        assert node("Bunko: Classics with Ruby") is not None
        scroll_to("Results")
        assert "Not connected" in ET.tostring(tree(), encoding="unicode")
        capture("android-results")
        scroll_to("Read published text")
        tap("Read published text")
        scroll_to("Hide published text")
        capture("android-published-copy")
        tap("Hide published text")
        scroll_to("Share public link…")
        tap("Share public link…")
        # Inspect only the system share sheet. Never select a recipient or send.
        share_tree = tree()
        assert any(n.get("package") == "com.android.intentresolver" and n.get("text") == "Sharing link"
                   for n in share_tree.iter("node")), "Native share sheet did not open"
        capture("android-share-sheet")
        adb("shell", "input", "keyevent", "4")
        adb("shell", "input", "keyevent", "4")
        assert node("Products") is not None
        tap("L & N: Speech Practice")
        assert node("Open google") is not None
        capture("android-landn")
        result = {"status": "passed", "snapshot_products": 2, "native_share_sheet_opened": True,
                  "share_recipient_selected": False, "public_posts_sent": 0,
                  "physical_device_tested": False, "ios_tested": False}
        (evidence / "android-result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
    except Exception:
        capture("android-failure")
        raise
    finally:
        adb("shell", "am", "force-stop", PACKAGE)


if __name__ == "__main__":
    main()
