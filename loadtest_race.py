"""
Teste de RACE em valvula_criar:  exists()->save() (TOCTOU) + gerar_codigo().

Estrategia:
  - clona uma valvula RETENCAO existente (spec valida, sem regra _parse_diametro)
  - muta `diametro` p/ uma tag UNICA -> spec inedita (nenhuma valvula tem essa ainda)
  - N sessoes logadas postam a MESMA spec inedita AO MESMO TEMPO (Barrier)

Resultado CORRETO:
  - exatamente 1x 200 (success) + (N-1)x 409 (duplicata)
  - no banco: exatamente 1 valvula com a tag

BUG de concorrencia (TOCTOU) se:
  - >1 success (200), ou
  - >1 valvula inserida com a tag, ou
  - codigos repetidos entre os successes, ou
  - qualquer 500

Uso: python loadtest_race.py        (LOADTEST_URL, LOADTEST_N como no loadtest.py)
"""

import os
import time
import uuid
import threading
import concurrent.futures as cf
from collections import Counter

import requests

BASE = os.environ.get("LOADTEST_URL", "http://127.0.0.1:8000").rstrip("/")
N = int(os.environ.get("LOADTEST_N", "10"))
PASSWORD = "LoadTest!2026xyz"
RUN = uuid.uuid4().hex[:8]
TAG = f"Z{RUN[:6]}"          # diametro unico, <=10 chars
TIMEOUT = 60


def csrf(session, path="/auth/"):
    session.get(f"{BASE}{path}", timeout=TIMEOUT)
    return session.cookies.get("csrftoken", "")


def confirmed_users(n):
    """Cadastra + confirma n usuarios via HTTP (precisa DEBUG=True)."""
    emails = [f"race_{RUN}_{i}@test.local" for i in range(n)]
    for e in emails:
        requests.post(f"{BASE}/api/cadastro/", json={
            "nome": f"Race {e}", "email": e,
            "password": PASSWORD, "password_confirm": PASSWORD}, timeout=TIMEOUT)
    r = requests.get(f"{BASE}/api/debug/verification-tokens/", timeout=TIMEOUT)
    pend = {u["email"]: u["token"] for u in r.json().get("usuarios_pendentes", [])}
    for e in emails:
        if e in pend:
            requests.get(f"{BASE}/verificar-email/{pend[e]}/", timeout=TIMEOUT)
    return emails


def logged_session(email):
    s = requests.Session()
    tok = csrf(s)
    s.post(f"{BASE}/api/login/", json={"email": email, "password": PASSWORD},
           headers={"X-CSRFToken": tok, "Referer": BASE}, timeout=TIMEOUT)
    return s, s.cookies.get("csrftoken", tok)


def build_new_spec():
    """Clona uma RETENCAO e troca diametro -> spec inedita."""
    vs = requests.get(f"{BASE}/api/valvulas/", timeout=TIMEOUT).json()["valvulas"]
    tmpl = next((v for v in vs if v["tipo_valvula"] == "RETENCAO"), vs[0])
    detail = requests.get(f"{BASE}/api/valvulas/{tmpl['id']}/", timeout=TIMEOUT).json()
    payload = {k: v for k, v in detail.items()
               if k not in ("id", "codigo", "tipo_label", "projeto_nome", "criado_em")}
    payload["diametro"] = TAG                  # <- torna a spec unica
    return payload, tmpl["tipo_valvula"]


def count_with_tag():
    vs = requests.get(f"{BASE}/api/valvulas/", timeout=TIMEOUT).json()["valvulas"]
    return [v for v in vs if v.get("diametro") == TAG]


def main():
    print(f"alvo={BASE}  N={N}  tag(diametro)={TAG}")
    payload, tipo = build_new_spec()
    print(f"template tipo={tipo}; spec inedita pronta (diametro={TAG})")

    pre = count_with_tag()
    if pre:
        print(f"! ja existem {len(pre)} valvulas com a tag (inesperado). abortando.")
        return

    emails = confirmed_users(N)
    sessions = [logged_session(e) for e in emails]

    barrier = threading.Barrier(N)
    results = []

    def worker(item):
        sess, tok = item
        barrier.wait()                          # todos disparam juntos
        t0 = time.perf_counter()
        try:
            r = sess.post(f"{BASE}/api/valvulas/criar/", json=payload,
                          headers={"X-CSRFToken": tok, "Referer": BASE}, timeout=TIMEOUT)
            dt = time.perf_counter() - t0
            codigo = None
            try:
                j = r.json()
                codigo = j.get("valvula", {}).get("codigo")
            except Exception:
                pass
            return (r.status_code, codigo, dt)
        except Exception as e:
            return ("EXC", f"{type(e).__name__}: {e}", time.perf_counter() - t0)

    with cf.ThreadPoolExecutor(max_workers=N) as ex:
        results = list(ex.map(worker, sessions))

    status_counts = Counter(r[0] for r in results)
    successes = [r for r in results if r[0] == 200]
    codigos = [r[1] for r in successes]
    post = count_with_tag()

    print("\n--- RESULTADO ---")
    print(f"status     : {dict(status_counts)}")
    print(f"successes  : {len(successes)}  codigos={codigos}")
    print(f"no banco   : {len(post)} valvula(s) com diametro={TAG} "
          f"(codigos={[v['codigo'] for v in post]})")

    ok = (len(successes) == 1 and len(post) == 1 and len(set(codigos)) == len(codigos)
          and "EXC" not in status_counts and 500 not in status_counts)
    if ok:
        print("\nVEREDITO: OK — sem race. 1 insert, resto 409. Guarda de duplicata segura sob concorrencia.")
    else:
        print("\nVEREDITO: RACE / BUG detectado!")
        if len(successes) > 1:
            print(f"  - {len(successes)} successes (esperado 1) -> TOCTOU em exists()->save()")
        if len(post) > 1:
            print(f"  - {len(post)} linhas inseridas (esperado 1) -> insert duplicado escapou")
        if len(set(codigos)) != len(codigos):
            print(f"  - codigos repetidos -> race em gerar_codigo()")
        if 500 in status_counts or "EXC" in status_counts:
            print(f"  - erros 500/excecao sob carga")


if __name__ == "__main__":
    main()