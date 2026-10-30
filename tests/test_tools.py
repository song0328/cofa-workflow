import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'tools'/f'{name}.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

security, csv_tool, compare = map(load, ['security_check', 'csv_check', 'compare_json'])

class ToolsTest(unittest.TestCase):
    def test_secret_values_never_appear_in_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = 'gh' + 'p_' + 'AbCd1234'*5
            (root/'config.txt').write_text('token='+secret, encoding='utf-8')
            (root/'.env').write_text('private', encoding='utf-8')
            findings, skipped = security.scan(root)
            self.assertEqual({x['kind'] for x in findings}, {'github-token', 'environment-file'})
            self.assertNotIn(secret, repr((findings, skipped)))

    def test_limits_and_outside_link_are_not_silently_scanned(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            (root/'large').write_bytes(b'x'*(security.LIMIT+1))
            target = Path(outside)/'secret'; target.write_text('outside')
            try:
                (root/'link').symlink_to(target)
            except OSError:
                pass  # Windows without symlink privilege still tests the size bound.
            findings, skipped = security.scan(root)
            self.assertEqual(findings, [])
            self.assertIn('over-1MiB', {x['reason'] for x in skipped})
            if (root/'link').is_symlink():
                self.assertIn('linked-file', {x['reason'] for x in skipped})

    def test_csv_reports_duplicates_nonfinite_and_shape_without_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'rows.csv'
            path.write_text('\ufeffid,amount\nprivate-id,3\nprivate-id,NaN\n,2\nshort\n', encoding='utf-8')
            result = csv_tool.inspect(path, ['id'], ['amount'])
            self.assertEqual(result['rows'], 4)
            self.assertEqual({x['kind'] for x in result['issues']}, {'duplicate-key','invalid-number','blank-key','column-count'})
            self.assertNotIn('private-id', repr(result))
            with self.assertRaises(ValueError):
                csv_tool.inspect(path, ['nonexistent'])

    def test_strict_json_preserves_types_order_and_hides_values(self):
        self.assertTrue(compare.differences({'flag':True}, {'flag':1}))
        self.assertTrue(compare.differences([1,2], [2,1]))
        self.assertFalse(compare.differences({'a':1,'b':2}, {'b':2,'a':1}))
        self.assertNotIn('private-value', repr(compare.differences({'private-value':1}, {})))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            for content in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}']:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    compare.read(path)

if __name__ == '__main__':
    unittest.main()
