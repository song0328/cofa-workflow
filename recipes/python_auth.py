"""인증·권한 틀 (Python 3.9+ 표준 라이브러리만)
과제 계약에 맞게 복사해 고쳐 쓴다. 과제 파일이 키트 경로를 import하지 않는다.
역할 이름·오류 코드·401/403/404 선택은 과제 README·담당자 답대로 바꾼다.
자체 확인: python3 python_auth.py   (마지막 줄 ok)

핸들러: try: s = get_session(token_from_headers(self.headers)); require_role(s, {"operator"})
        except AuthError as e: return self.send_json(e.status, {"error": e.code})
사용자 id·역할은 세션에서만 꺼낸다. 본문·쿼리의 userId·role은 믿지 않는다.
"""
import hashlib
import hmac
import secrets
import threading
import time

_SCRYPT = dict(n=2**14, r=8, p=1, dklen=32)   # 메모리 약 16MB
_PBKDF2_ROUNDS = 200_000                       # scrypt가 없는 빌드용
SESSION_TTL = 8 * 3600                         # 초. README·담당자 답이 있으면 그대로


class AuthError(Exception):
    """status 401(로그인 필요)·403(권한 없음)·404(존재 숨김). 핸들러가 잡아 응답으로 바꾼다."""

    def __init__(self, status, code):
        super().__init__(code)
        self.status, self.code = status, code


# ── 비밀번호: 저장 형식 "방식$소금hex$해시hex" ──
def _derive(scheme, password, salt):
    pw = password.encode("utf-8")
    if scheme == "scrypt":
        return hashlib.scrypt(pw, salt=salt, **_SCRYPT)
    if scheme == "pbkdf2":
        return hashlib.pbkdf2_hmac("sha256", pw, salt, _PBKDF2_ROUNDS)
    raise ValueError("unknown scheme")


def hash_password(password, scheme=None):
    scheme = scheme or ("scrypt" if hasattr(hashlib, "scrypt") else "pbkdf2")
    salt = secrets.token_bytes(16)                 # 해시마다 새 소금
    return f"{scheme}${salt.hex()}${_derive(scheme, password, salt).hex()}"


def verify_password(password, stored):
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
        actual = _derive(scheme, password, bytes.fromhex(salt_hex))
        expected = bytes.fromhex(digest_hex)
    except (ValueError, AttributeError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)   # 상수 시간 비교


# ── 세션: 메모리 dict. 재시작 뒤에도 로그인이 유지돼야 하면 DB 표로 옮긴다 ──
_sessions = {}   # token -> {"user_id", "role", "expires"}
_lock = threading.Lock()


def new_session(user_id, role, ttl=SESSION_TTL, now=None):
    token = secrets.token_urlsafe(32)              # 추측 불가 토큰
    now = time.time() if now is None else now
    with _lock:
        _sessions[token] = {"user_id": user_id, "role": role, "expires": now + ttl}
    return token


def get_session(token, now=None):
    now = time.time() if now is None else now
    with _lock:
        s = _sessions.get(token) if token else None
        if s and s["expires"] <= now:
            del _sessions[token]
            s = None
    if not s:
        raise AuthError(401, "LOGIN_REQUIRED")
    return dict(s)


def end_session(token):
    with _lock:
        _sessions.pop(token, None)


def token_from_headers(headers):
    auth = headers.get("Authorization") or ""
    return auth[7:].strip() if auth.startswith("Bearer ") else None


_dummy = []


def login(users, username, password):
    """users: {아이디: {"id", "role", "password_hash"}}.
    없는 아이디와 틀린 비밀번호를 같은 오류·비슷한 시간으로 (계정 존재 숨김)."""
    user = users.get(username)
    if not _dummy:
        _dummy.append(hash_password("dummy-password"))
    ok = verify_password(password, user["password_hash"] if user else _dummy[0])
    if not (user and ok):
        raise AuthError(401, "INVALID_CREDENTIALS")
    return new_session(user["id"], user["role"])


# ── 권한 검사: 모든 경로가 이 함수들을 지나게 ──
def require_role(session, allowed_roles):
    if not session:
        raise AuthError(401, "LOGIN_REQUIRED")
    if session["role"] not in allowed_roles:
        raise AuthError(403, "FORBIDDEN")
    return session


def own_only(session, owner_id, staff_roles=(), hide=False):
    """본인 자료만. staff_roles는 남의 자료도 통과. hide=True면 404로 존재 자체를 숨긴다(README대로)."""
    if not session:
        raise AuthError(401, "LOGIN_REQUIRED")
    if session["role"] in staff_roles or str(session["user_id"]) == str(owner_id):  # id 타입 차이 흡수
        return session
    raise AuthError(404, "NOT_FOUND") if hide else AuthError(403, "FORBIDDEN")


def pick(record, fields):
    """역할별로 보낼 필드만 서버에서 고른다(화면에서 숨기는 것으로 대신하지 않는다)."""
    return {k: record[k] for k in fields if k in record}


if __name__ == "__main__":
    h = hash_password("pw-1")
    assert verify_password("pw-1", h) and not verify_password("pw-2", h)
    users = {"op": {"id": 1, "role": "operator", "password_hash": h}}
    assert require_role(get_session(login(users, "op", "pw-1")), {"operator"})["user_id"] == 1
    m = get_session(new_session(7, "member"))
    for call, status in [(lambda: login(users, "nobody", "pw-1"), 401),
                         (lambda: get_session(new_session(7, "member", ttl=1, now=0)), 401),
                         (lambda: require_role(m, {"operator"}), 403),
                         (lambda: own_only(m, 8), 403), (lambda: own_only(m, 8, hide=True), 404)]:
        try:
            call(); raise AssertionError("not rejected")
        except AuthError as e:
            assert e.status == status, (e.status, status)
    assert own_only(m, "7") and pick({"id": 1, "cost": 9}, ["id"]) == {"id": 1}
    print("ok")
