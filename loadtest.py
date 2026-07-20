"""
Teste de carga / concorrencia para Imex Solutions.

4 cenarios, cada um com N usuarios disparando AO MESMO TEMPO (threading.Barrier):
  A) cadastro de contas simultaneo      -> POST /api/cadastro/
  B) login simultaneo                   -> POST /api/login/
  C) gerar/baixar PDF+Excel simultaneo  -> GET  /valvulas/<pk>/pdf/   ("instalar itens")
  D) cadastrar valvulas simultaneo      -> POST /api/valvulas/criar/

Uso:
  python loadtest.py                 # tudo, contra http://127.0.0.1:8000, N=10
  LOADTEST_URL=http://127.0.0.1:8000 LOADTEST_N=10 python loadtest.py
  python loadtest.py A C              # so cenarios A e C

Requisitos:
  - servidor rodando LOCAL (python manage.py runserver)
  - DEBUG=True  (cenario B usa /api/debug/verification-tokens/ para confirmar contas)
  - pip install requests
"""

import os
import sys
import time
import uuid
import threading
import statistics
import concurrent.futures as cf

import requests

BASE = os.environ.get("LOADTEST_URL", "http://127.0.0.1:8000").rstrip("/")
N = int(os.environ.get("LOADTEST_N", "10"))
PASSWORD = "LoadTest!2026xyz"          # passa nos validadores (>=8, nao numerica, nao comum)
RUN = uuid.uuid4().hex[:8]             # isola emails entre execucoes
TIMEOUT = 60


# ---------------------------------------------------------------- helpers ----
def csrf(session, path="/auth/"):
    """GET numa pagina pra receber o cookie csrftoken; retorna o valor."""
    session.get(f"{BASE}{path}", timeout=TIMEOUT)
    return session.cookies.get("csrftoken", "")


def timed(fn):
    """Executa fn(), retorna (ok, status, segundos, nota)."""
    t0 = time.perf_counter()
    try:
        status, note = fn()
        return True, status, time.perf_counter() - t0, note
    except Exception as e:
        return False, None, time.perf_counter() - t0, f"{type(e).__name__}: {e}"


def fire(label, worker, items):
    """Dispara len(items) threads ao mesmo tempo via Barrier. worker(item)->fn p/ timed."""
    n = len(items)
    barrier = threading.Barrier(n)
    results = []

    def run(item):
        barrier.wait()                 # todos esperam, depois disparam juntos
        return timed(worker(item))

    wall0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        results = list(ex.map(run, items))
    wall = time.perf_counter() - wall0
    report(label, results, wall)
    return results


def report(label, results, wall):
    lat = [r[2] for r in results]
    by_status = {}
    errors = []
    for ok, status, secs, note in results:
        key = status if ok else "EXC"
        by_status[key] = by_status.get(key, 0) + 1
        if not ok or (isinstance(status, int) and status >= 400):
            errors.append((status, note))
    print(f"\n=== {label} ===")
    print(f"  requisicoes : {len(results)}   wallclock: {wall:.2f}s "
          f"(throughput ~{len(results)/wall:.1f} req/s)")
    print(f"  latencia    : min {min(lat):.2f}s | mediana {statistics.median(lat):.2f}s "
          f"| max {max(lat):.2f}s")
    print(f"  por status  : " + ", ".join(f"{k}:{v}" for k, v in sorted(by_status.items(), key=str)))
    for status, note in errors[:8]:
        print(f"    - [{status}] {str(note)[:160]}")


# --------------------------------------------------------------- cenarios ----
def scenario_signup():
    emails = [f"load_{RUN}_{i}@test.local" for i in range(N)]

    def worker(email):
        def fn():
            s = requests.Session()
            r = s.post(f"{BASE}/api/cadastro/", json={
                "nome": f"Load {email}",
                "email": email,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            }, timeout=TIMEOUT)
            return r.status_code, r.text[:120]
        return fn

    fire(f"A) CADASTRO simultaneo  (N={N})", worker, emails)
    return emails


def seed_confirmed_users(emails):
    """Garante N contas confirmadas (sequencial). Reaproveita as do cenario A se existirem."""
    # 1) cadastra as que faltam
    for email in emails:
        requests.post(f"{BASE}/api/cadastro/", json={
            "nome": f"Load {email}", "email": email,
            "password": PASSWORD, "password_confirm": PASSWORD,
        }, timeout=TIMEOUT)
    # 2) pega tokens (DEBUG) e confirma cada um
    r = requests.get(f"{BASE}/api/debug/verification-tokens/", timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  ! nao consegui tokens (HTTP {r.status_code}). DEBUG=True? "
              f"resposta: {r.text[:120]}")
        return []
    pend = {u["email"]: u["token"] for u in r.json().get("usuarios_pendentes", [])}
    confirmed = []
    for email in emails:
        token = pend.get(email)
        if token:
            requests.get(f"{BASE}/verificar-email/{token}/", timeout=TIMEOUT)
        confirmed.append(email)
    return confirmed


def scenario_login(emails):
    confirmed = seed_confirmed_users(emails)
    if not confirmed:
        print("  ! pulando login: sem usuarios confirmados")
        return

    def worker(email):
        def fn():
            s = requests.Session()
            token = csrf(s)
            r = s.post(f"{BASE}/api/login/",
                       json={"email": email, "password": PASSWORD},
                       headers={"X-CSRFToken": token, "Referer": BASE},
                       timeout=TIMEOUT)
            return r.status_code, r.text[:120]
        return fn

    fire(f"B) LOGIN simultaneo  (N={N})", worker, confirmed)


def get_valve_ids():
    r = requests.get(f"{BASE}/api/valvulas/", timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    return [v["id"] for v in r.json().get("valvulas", [])]


def scenario_pdf():
    ids = get_valve_ids()
    if not ids:
        print("\n=== C) PDF+EXCEL ===\n  ! nenhuma valvula no banco. "
              "Cadastre 1 valvula pela UI e rode de novo.")
        return
    pk = ids[0]
    print(f"  (gerando PDF+Excel da valvula id={pk}, {N}x simultaneo)")

    def worker(_i):
        def fn():
            r = requests.get(f"{BASE}/valvulas/{pk}/pdf/", timeout=TIMEOUT)
            ct = r.headers.get("Content-Type", "")
            return r.status_code, f"{ct} {len(r.content)}B"
        return fn

    fire(f"C) PDF+EXCEL simultaneo  (N={N})", worker, list(range(N)))


def scenario_valve_create(emails):
    confirmed = seed_confirmed_users(emails)
    if not confirmed:
        print("\n=== D) CADASTRO VALVULA ===\n  ! sem usuarios confirmados; pulando")
        return
    ids = get_valve_ids()
    if not ids:
        print("\n=== D) CADASTRO VALVULA ===\n  ! nenhuma valvula modelo no banco. "
              "Cadastre 1 valvula pela UI e rode de novo.")
        return

    # clona uma valvula existente como payload valido (mesma spec p/ todos os threads)
    detail = requests.get(f"{BASE}/api/valvulas/{ids[0]}/", timeout=TIMEOUT).json()
    payload = {k: v for k, v in detail.items()
               if k not in ("id", "codigo", "tipo_label", "projeto_nome", "criado_em")}

    # uma sessao logada por thread (precisa auth + csrf)
    def make_logged_session(email):
        s = requests.Session()
        token = csrf(s)
        s.post(f"{BASE}/api/login/", json={"email": email, "password": PASSWORD},
               headers={"X-CSRFToken": token, "Referer": BASE}, timeout=TIMEOUT)
        return s, s.cookies.get("csrftoken", token)

    sessions = [make_logged_session(e) for e in confirmed]
    print(f"\n  (10 threads postam a MESMA spec -> esperado: 1x success(200) + resto duplicata(409).")
    print(f"   mais de 1 success, ou 500, ou codigos repetidos = RACE em exists()/gerar_codigo)")

    def worker(item):
        sess, tok = item
        def fn():
            r = sess.post(f"{BASE}/api/valvulas/criar/", json=payload,
                          headers={"X-CSRFToken": tok, "Referer": BASE}, timeout=TIMEOUT)
            try:
                j = r.json()
                note = j.get("valvula", {}).get("codigo") or str(j.get("errors") or j)[:120]
            except Exception:
                note = r.text[:120]
            return r.status_code, note
        return fn

    fire(f"D) CADASTRO VALVULA simultaneo  (N={N})", worker, sessions)


# ------------------------------------------------------------------- main ----
def main():
    pick = [a.upper() for a in sys.argv[1:]] or ["A", "B", "C", "D"]
    print(f"alvo={BASE}  N={N}  run={RUN}")
    try:
        requests.get(BASE, timeout=10)
    except Exception as e:
        print(f"! servidor inacessivel em {BASE}: {e}")
        sys.exit(1)

    emails = [f"load_{RUN}_{i}@test.local" for i in range(N)]
    if "A" in pick:
        emails = scenario_signup()
    if "B" in pick:
        scenario_login(emails)
    if "C" in pick:
        scenario_pdf()
    if "D" in pick:
        scenario_valve_create(emails)
    print("\nfim.")


if __name__ == "__main__":
    main()
