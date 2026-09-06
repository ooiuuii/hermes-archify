"""Regression coverage for the ASS event-column alignment used by the demos."""
import importlib.util
from pathlib import Path
import unittest


builder_path = Path(__file__).resolve().parents[1] / 'v2' / 'build_video.py'
spec = importlib.util.spec_from_file_location('demo_video_builder', builder_path)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AssCaptionTests(unittest.TestCase):
    def parse_event(self, caption):
        document = builder.serialize_ass_captions([
            ('0:00:00.45', '0:00:03.20', caption),
        ])
        format_line, dialogue_line = document.split('[Events]\n', 1)[1].splitlines()
        fields = format_line.removeprefix('Format: ').split(',')
        self.assertEqual(fields, [
            'Layer', 'Start', 'End', 'Style', 'Name',
            'MarginL', 'MarginR', 'MarginV', 'Effect', 'Text',
        ])
        # ASS only splits the metadata fields: commas in the final Text are literal.
        values = dialogue_line.removeprefix('Dialogue: ').split(',', len(fields) - 1)
        self.assertEqual(len(values), len(fields))
        return dict(zip(fields, values))

    def test_empty_effect_does_not_prefix_caption_with_comma(self):
        caption = '先选起点，再选终点。'
        event = self.parse_event(caption)
        self.assertEqual(event['Effect'], '')
        self.assertEqual(event['Text'], caption)
        self.assertEqual(event['Start'], '0:00:00.45')
        self.assertEqual(event['End'], '0:00:03.20')

    def test_authored_commas_and_line_breaks_are_preserved(self):
        caption = ',这是台词里的逗号，English, too。\n下一行。'
        event = self.parse_event(caption)
        self.assertEqual(event['Text'], caption.replace('\n', r'\N'))


if __name__ == '__main__':
    unittest.main()
