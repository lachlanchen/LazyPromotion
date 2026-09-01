import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import lkt_delivery


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "lkt-collection-fit-intake.example.json"
OPERATOR_EXAMPLE = ROOT / "examples" / "lkt-collection-fit-intake.operator.example.json"


def example_intake() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class LktDeliveryTests(unittest.TestCase):
    def test_public_example_renders_deterministically_with_truth_boundaries(self):
        intake = lkt_delivery.load_intake(EXAMPLE)
        first = lkt_delivery.render_delivery_packet(intake)
        second = lkt_delivery.render_delivery_packet(copy.deepcopy(intake))

        self.assertEqual(first, second)
        self.assertIn("SANITIZED PLANNING PACKET; NOT A CUSTOMER RESULT", first)
        self.assertIn("cannot independently prove de-identification", first)
        self.assertIn("Every representative-proof step below is planned", first)
        self.assertIn("Commercial outcomes are outside this packet", first)
        self.assertIn("## Data, privacy, and citation map", first)
        self.assertIn("## Representative-proof plan", first)
        self.assertIn("## Go/no-go boundary", first)
        self.assertIn("## Fixed exclusions", first)
        self.assertIn("GO TO REPRESENTATIVE-PROOF PLAN", first)
        self.assertIn("19,119", first)

    def test_operator_prepared_metadata_path_can_drive_real_fulfillment_safely(self):
        intake = lkt_delivery.load_intake(OPERATOR_EXAMPLE)
        packet = lkt_delivery.render_delivery_packet(intake)

        self.assertEqual(intake["input_classification"], "sanitized_metadata_only")
        self.assertEqual(intake["source_status"], "operator_prepared_fit_summary")
        self.assertIn("OPERATOR-PREPARED FIT SUMMARY; METADATA DECLARATIONS ONLY", packet)
        self.assertIn("cannot independently prove de-identification", packet)
        self.assertIn("Every representative-proof step below is planned", packet)
        self.assertIn("Commercial outcomes are outside this packet", packet)
        self.assertIn("**GO TO REPRESENTATIVE-PROOF PLAN**", packet)
        self.assertNotIn("NOT A CUSTOMER RESULT", packet)

    def test_classification_and_source_status_pairing_fails_closed(self):
        intake = example_intake()
        intake["input_classification"] = "sanitized_metadata_only"
        with self.assertRaisesRegex(
            lkt_delivery.IntakeValidationError, "operator_prepared_fit_summary"
        ):
            lkt_delivery.validate_intake(intake)

        intake = example_intake()
        intake["source_status"] = "operator_prepared_fit_summary"
        with self.assertRaisesRegex(
            lkt_delivery.IntakeValidationError, "sanitized_metadata_only"
        ):
            lkt_delivery.validate_intake(intake)

    def test_unconfirmed_rights_render_no_go_without_hiding_the_reason(self):
        intake = example_intake()
        intake["rights"] = {"status": "unconfirmed", "basis": "unknown"}
        packet = lkt_delivery.render_delivery_packet(intake)

        self.assertIn("**NO-GO**", packet)
        self.assertIn("source rights are not confirmed", packet)

    def test_bounded_privacy_and_citation_gates_each_fail_to_no_go(self):
        cases = (
            (("collection", "bounded"), False, "collection is not bounded"),
            (("privacy", "processing_boundary"), "unresolved", "privacy boundary is unresolved"),
            (("citation", "page_or_locator_available"), False, "record locator is unavailable"),
        )
        for path, value, reason in cases:
            with self.subTest(path=path):
                intake = example_intake()
                intake[path[0]][path[1]] = value
                packet = lkt_delivery.render_delivery_packet(intake)
                self.assertIn("**NO-GO**", packet)
                self.assertIn(reason, packet)

    def test_excluded_work_renders_separate_scope(self):
        intake = example_intake()
        intake["collection"]["format"] = "image_only_pdf"
        intake["requested_scope"]["custom_ocr"] = True
        packet = lkt_delivery.render_delivery_packet(intake)

        self.assertIn("**SEPARATE SCOPE**", packet)
        self.assertIn("custom OCR is outside the sprint", packet)

    def test_source_content_or_customer_fields_fail_closed(self):
        for field, value in (
            ("source_excerpt", "private source text"),
            ("customer_email", "person@example.test"),
            ("payment_status", "paid"),
        ):
            with self.subTest(field=field):
                intake = example_intake()
                intake[field] = value
                with self.assertRaisesRegex(lkt_delivery.IntakeValidationError, "unsupported fields"):
                    lkt_delivery.validate_intake(intake)

    def test_payload_or_identifier_flags_fail_closed(self):
        for field in ("sample_payload_included", "sensitive_identifiers_included"):
            with self.subTest(field=field):
                intake = example_intake()
                intake["privacy"][field] = True
                with self.assertRaisesRegex(lkt_delivery.IntakeValidationError, field):
                    lkt_delivery.validate_intake(intake)

    def test_duplicate_json_fields_are_rejected(self):
        content = EXAMPLE.read_text(encoding="utf-8").replace(
            '"schema_version": 1,', '"schema_version": 1,\n  "schema_version": 1,', 1
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text(content, encoding="utf-8")
            with self.assertRaisesRegex(lkt_delivery.IntakeValidationError, "duplicate JSON field"):
                lkt_delivery.load_intake(path)

    def test_cli_stdout_matches_library_renderer(self):
        expected = lkt_delivery.render_delivery_packet(lkt_delivery.load_intake(EXAMPLE))
        output = io.StringIO()
        with redirect_stdout(output):
            result = lkt_delivery.main([str(EXAMPLE)])

        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), expected)

    def test_schema_and_example_expose_no_free_form_customer_data_fields(self):
        schema = json.loads(
            (ROOT / "schemas" / "lkt-collection-fit-intake.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        for path in (EXAMPLE, OPERATOR_EXAMPLE):
            with self.subTest(path=path.name):
                lkt_delivery.load_intake(path)
                serialized = json.dumps(
                    {"schema": schema, "example": json.loads(path.read_text(encoding="utf-8"))}
                )
                for forbidden in (
                    "email",
                    "name",
                    "source_excerpt",
                    "source_path",
                    "payment",
                    "lead",
                ):
                    self.assertNotIn(f'"{forbidden}"', serialized)


if __name__ == "__main__":
    unittest.main()
