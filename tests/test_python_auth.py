import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('python_auth', ROOT/'recipes'/'python_auth.py')
auth = importlib.util.module_from_spec(spec); spec.loader.exec_module(auth)

class PythonAuthTest(unittest.TestCase):
    def rejected(self, call):
        with self.assertRaises(auth.AuthError) as ctx:
            call()
        return ctx.exception.status, ctx.exception.code

    def test_hash_roundtrip_wrong_password_and_fallback(self):
        for scheme in [None, 'pbkdf2']:
            stored = auth.hash_password('correct horse', scheme=scheme)
            self.assertNotIn('correct horse', stored)
            self.assertTrue(auth.verify_password('correct horse', stored))
            self.assertFalse(auth.verify_password('correct horsE', stored))
        for broken in ['', 'plain', 'scrypt$zz$zz', None]:
            self.assertFalse(auth.verify_password('x', broken))

    def test_salt_differs_per_hash(self):
        a, b = auth.hash_password('same'), auth.hash_password('same')
        self.assertNotEqual(a, b)
        self.assertNotEqual(a.split('$')[1], b.split('$')[1])

    def test_session_expiry_and_unknown_token(self):
        token = auth.new_session(1, 'member', ttl=60, now=1000)
        self.assertEqual(auth.get_session(token, now=1059)['user_id'], 1)
        self.assertEqual(self.rejected(lambda: auth.get_session(token, now=1060)), (401, 'LOGIN_REQUIRED'))
        self.assertEqual(self.rejected(lambda: auth.get_session(token, now=1000))[0], 401)  # 만료 시 삭제됨
        for bad in [None, '', 'guess']:
            self.assertEqual(self.rejected(lambda: auth.get_session(bad))[0], 401)
        live = auth.new_session(2, 'member'); auth.end_session(live)
        self.assertEqual(self.rejected(lambda: auth.get_session(live))[0], 401)

    def test_require_role(self):
        member = auth.get_session(auth.new_session(1, 'member'))
        self.assertEqual(self.rejected(lambda: auth.require_role(member, {'operator'})), (403, 'FORBIDDEN'))
        self.assertEqual(self.rejected(lambda: auth.require_role(None, {'operator'}))[0], 401)
        self.assertIs(auth.require_role(member, {'member', 'operator'}), member)

    def test_own_only(self):
        a = auth.get_session(auth.new_session(1, 'member'))
        op = auth.get_session(auth.new_session(9, 'operator'))
        self.assertIs(auth.own_only(a, 1), a)
        self.assertIs(auth.own_only(a, '1'), a)
        self.assertEqual(self.rejected(lambda: auth.own_only(a, 2))[0], 403)
        self.assertEqual(self.rejected(lambda: auth.own_only(a, 2, hide=True))[0], 404)
        self.assertIs(auth.own_only(op, 2, staff_roles={'operator'}), op)
        self.assertEqual(self.rejected(lambda: auth.own_only(op, 2))[0], 403)

    def test_login_hides_account_existence_and_pick_filters(self):
        users = {'kim': {'id': 3, 'role': 'member', 'password_hash': auth.hash_password('pw')}}
        self.assertEqual(auth.get_session(auth.login(users, 'kim', 'pw'))['role'], 'member')
        self.assertEqual(self.rejected(lambda: auth.login(users, 'kim', 'bad')),
                         self.rejected(lambda: auth.login(users, 'lee', 'pw')))
        self.assertEqual(auth.token_from_headers({'Authorization': 'Bearer abc'}), 'abc')
        self.assertIsNone(auth.token_from_headers({}))
        self.assertEqual(auth.pick({'id': 1, 'password_hash': 'x'}, ['id', 'name']), {'id': 1})

if __name__ == '__main__':
    unittest.main()
