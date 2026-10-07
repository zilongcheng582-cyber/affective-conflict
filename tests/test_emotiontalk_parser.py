import unittest

from emotiontalk_controlled_parser_v1 import parse_label


class EmotionTalkParserContractTests(unittest.TestCase):
    def assertParsed(self, raw, label, status):
        result = parse_label(raw)
        self.assertEqual(result["parsed_label"], label)
        self.assertEqual(result["parser_status"], status)
        self.assertEqual(result["raw_text"], raw)

    def test_canonical(self):
        self.assertParsed("happy", "happy", "OK")

    def test_case_insensitive(self):
        self.assertParsed("Happy", "happy", "OK")

    def test_outer_whitespace(self):
        self.assertParsed(" happy ", "happy", "OK")

    def test_sentence_is_rejected(self):
        # Only a bare label plus outer whitespace is accepted.
        self.assertParsed("The answer is happy.", None, "PARSE_FAIL")

    def test_unknown_text(self):
        self.assertParsed("joyful", None, "PARSE_FAIL")

    def test_multiple_conflicting_labels(self):
        self.assertParsed("happy sad", None, "PARSE_FAIL")


if __name__ == "__main__":
    unittest.main()
