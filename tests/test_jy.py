import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('jy', Path(__file__).resolve().parents[1] / 'lib/jy.py')
jy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jy)


class BrowserTests(unittest.TestCase):
    def test_one_level_filter_and_drill(self):
        value = {'name': 'xxx', 'resources': {'request': {'cpu': '10m'}}, 'service': {'resources': 1}}
        self.assertEqual(jy.matching(value, 'res'), ['resources'])
        self.assertEqual(jy.matching(value, 'cpu'), [])
        self.assertEqual(jy.scoped(value, ['resources', 'request', 'cpu']), '10m')
        self.assertNotIn('service', jy.preview(value, 'res', 'yaml'))
        self.assertIn('\x1b[31mres\x1b[0mources:', jy.preview(value, 'res', 'yaml'))

    def test_literal_unusual_keys_and_arrays(self):
        key = 'a.b[0]/"\n$(touch nope)'
        value = {key: [{'x': False}, None, 0]}
        self.assertIsNone(jy.scoped(value, [key, 1]))
        self.assertEqual(jy.scoped(value, [key, 2]), 0)
        self.assertEqual(jy.scoped(value, [key, 0, 'x']), False)
        self.assertEqual(jy.matching(value, '['), [key])

    def test_yaml_and_json(self):
        value, mode = jy.decode('resources:\n  request:\n    cpu: 10m\n', 'auto')
        self.assertEqual(mode, 'yaml')
        self.assertEqual(jy.scoped(value, ['resources', 'request']), {'cpu': '10m'})
        self.assertEqual(jy.decode('{"a":null}', 'auto'), ({'a': None}, 'json'))

    def test_reject_streams_and_invalid(self):
        for text, mode in [('', 'auto'), ('{} {}', 'json'), ('a: 1\n---\nb: 2', 'yaml'), ('[', 'json')]:
            with self.subTest(text=text), self.assertRaises(Exception):
                jy.decode(text, mode)

    def test_empty_and_scalars(self):
        for value in [None, False, 0, '', {}, []]:
            self.assertEqual(jy.keys(value), [])
            self.assertEqual(jy.scoped(value, []), value)
