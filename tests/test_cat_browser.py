import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
import cat_browser as browser


class FileBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.file = self.root / 'values.yaml'
        self.file.write_text('resources:\n  request:\n    cpu: 10m\n')

    def test_select_file_then_automatic_search(self):
        with patch.object(browser.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='0\t"values.yaml"\n')):
            selected = browser.pick(self.root, '80%')
        self.assertEqual(selected, self.file)
        with patch.object(browser.jy, 'browse') as browse:
            browser.open_file(selected, '80%')
        self.assertEqual(browse.call_args.args, ({'resources': {'request': {'cpu': '10m'}}}, 'yaml', '80%'))

    def test_plain_text_and_malformed_yaml_remain_readable(self):
        for filename, text in [('readme.txt', 'hello world'), ('bad.yaml', 'a: [')]:
            path = self.root / filename
            path.write_text(text)
            with patch.object(browser, 'text_view') as view, patch.object(browser.jy, 'browse') as browse:
                browser.open_file(path, '80%')
            view.assert_called_once()
            browse.assert_not_called()

    def test_detection_without_extension(self):
        self.assertEqual(browser.detect(Path('config'), '{"a":1}'), 'json')
        self.assertEqual(browser.detect(Path('config'), 'a:\n  b: 1\n'), 'yaml')
        self.assertEqual(browser.detect(Path('notes'), 'hello world'), 'text')

    def test_search_is_above_content(self):
        with patch.object(browser.jy, 'scoped', return_value={'a': 1}), patch.object(browser.jy.subprocess, 'run', return_value=SimpleNamespace(returncode=130)) as run:
            browser.jy.browse({'a': 1}, 'json', '80%', title='test.json')
        args = run.call_args.args[0]
        self.assertIn('--layout=reverse', args)
        self.assertIn('--preview-window=down,65%,border-top', args)
        self.assertIn('--prompt=jq . > ', args)

    def test_scalar_enter_stays_in_viewer(self):
        outputs = [SimpleNamespace(returncode=0, stdout='enter\n0\t"a"\n'), SimpleNamespace(returncode=130)]
        with patch.object(browser.jy, 'scoped', side_effect=[{'a': 1}, 1]), patch.object(browser.jy.subprocess, 'run', side_effect=outputs) as run:
            browser.jy.browse({'a': 1}, 'json', '80%')
        self.assertEqual(run.call_count, 2)
        self.assertIn('--prompt=jq .["a"] > ', run.call_args.args[0])
