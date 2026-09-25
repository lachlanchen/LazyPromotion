import hashlib
import json
from pathlib import Path
import plistlib
import unittest
import xml.etree.ElementTree as ET

import app_workspace

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT / "apps"


class NativePreviewTests(unittest.TestCase):
    def test_both_native_clients_bundle_the_exact_public_projection(self):
        snapshot = json.loads((APPS / "shared/workspace-preview.json").read_text())
        self.assertEqual(snapshot["workspace"], app_workspace.workspace())
        self.assertEqual(snapshot["fetchedAt"], "2026-09-25T19:37:21Z")
        for project in snapshot["workspace"]["projects"]:
            for post in project["publications"]:
                self.assertEqual(post["bodySha256"], hashlib.sha256(post["body"].encode()).hexdigest())

    def test_android_has_no_network_or_background_permissions(self):
        manifest = ET.parse(APPS / "android/app/src/main/AndroidManifest.xml").getroot()
        self.assertEqual(manifest.findall("uses-permission"), [])
        self.assertEqual(manifest.findall(".//service"), [])
        source = (APPS / "android/app/build.gradle.kts").read_text()
        self.assertIn('assets.srcDir("../../shared")', source)
        self.assertIn('applicationId = "art.lazying.promotion.preview"', source)

    def test_ios_project_references_real_sources_and_shared_snapshot(self):
        root = APPS / "ios"
        pbx = (root / "LazyPromotion.xcodeproj/project.pbxproj").read_text()
        for relative in ("LazyPromotion/LazyPromotionApp.swift", "LazyPromotion/Core/Workspace.swift",
                         "LazyPromotion/Info.plist", "LazyPromotion/PrivacyInfo.xcprivacy", "../shared/workspace-preview.json"):
            self.assertTrue((root / relative).is_file(), relative)
            self.assertIn(Path(relative).name, pbx)
        ET.parse(root / "LazyPromotion.xcodeproj/xcshareddata/xcschemes/LazyPromotion.xcscheme")
        with (root / "LazyPromotion/Info.plist").open("rb") as file:
            info = plistlib.load(file)
        self.assertNotIn("UIBackgroundModes", info)
        self.assertNotIn("NSAppTransportSecurity", info)
        with (root / "LazyPromotion/PrivacyInfo.xcprivacy").open("rb") as file:
            privacy = plistlib.load(file)
        self.assertFalse(privacy["NSPrivacyTracking"])

    def test_native_clients_do_not_embed_web_or_operator_runtime(self):
        for directory, extension in ((APPS / "android/app/src/main", "*.kt"), (APPS / "ios/LazyPromotion", "*.swift")):
            for path in directory.rglob(extension):
                source = path.read_text()
                for forbidden in ("WebView", "WKWebView", "127.0.0.1", "POSTIZ_API_KEY", "lazypromotion.sqlite", "/home/lachlan/"):
                    self.assertNotIn(forbidden, source, path)


if __name__ == "__main__":
    unittest.main()
