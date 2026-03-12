"""
setup_posthog.py — Integra PostHog no Prazu
Roda uma vez: python3 setup_posthog.py
"""
import os

# ─── 1. Criar web/templates/posthog_snippet.html ────────────────────────────
snippet = '''<!-- PostHog Analytics -->
<script>
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]);t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once registerSelf unregister unregisterSelf opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group identify setPersonProperties".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
  posthog.init('phc_b5QNBhNd37836VpfFn91Qjtvs6AJY1Mu1XTEEkT7Bxk', {
    api_host: 'https://us.i.posthog.com',
    person_profiles: 'identified_only',
    capture_pageview: true,
    capture_pageleave: true
  });
</script>
{% if advogado is defined and advogado %}
<script>
  posthog.identify('{{ advogado.id }}', {
    email: '{{ advogado.get("email", "") }}',
    nome: '{{ advogado.get("nome", "") }}',
    oab: '{{ advogado.get("numero_oab", "") }}'
  });
</script>
{% endif %}
'''

snippet_path = os.path.join("web", "templates", "posthog_snippet.html")
with open(snippet_path, "w") as f:
    f.write(snippet)
print(f"[OK] Criado: {snippet_path}")


# ─── 2. Adicionar include em todos os templates ─────────────────────────────
templates = [
    "landing.html",
    "cadastro.html",
    "login.html",
    "esqueci_senha.html",
    "onboarding.html",
    "dashboard.html",
    "plano_expirado.html",
    "termos.html",
    "privacidade.html",
    "configuracoes.html",
]

include_line = '  {% include "posthog_snippet.html" %}\n'

for tpl in templates:
    path = os.path.join("web", "templates", tpl)
    if not os.path.exists(path):
        print(f"[SKIP] {tpl} nao encontrado")
        continue

    with open(path, "r") as f:
        content = f.read()

    if "posthog_snippet" in content or "posthog.init" in content:
        print(f"[SKIP] {tpl} ja tem PostHog")
        continue

    if "</head>" in content:
        content = content.replace("</head>", include_line + "</head>", 1)
        with open(path, "w") as f:
            f.write(content)
        print(f"[OK] {tpl} — PostHog adicionado")
    else:
        print(f"[WARN] {tpl} — nao tem </head>")


# ─── 3. Adicionar import posthog no web/app.py ──────────────────────────────
app_path = os.path.join("web", "app.py")
with open(app_path, "r") as f:
    app_content = f.read()

if "import posthog" in app_content:
    print(f"[SKIP] web/app.py ja tem import posthog")
else:
    # Inserir depois de "import database_gcp as db"
    marker = "import database_gcp as db"
    posthog_block = '''import database_gcp as db

# ── PostHog Analytics ────────────────────────────────────────────────────────
import posthog
posthog.api_key = os.getenv("POSTHOG_API_KEY", "phc_b5QNBhNd37836VpfFn91Qjtvs6AJY1Mu1XTEEkT7Bxk")
posthog.host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")'''

    if marker in app_content:
        app_content = app_content.replace(marker, posthog_block, 1)
        with open(app_path, "w") as f:
            f.write(app_content)
        print(f"[OK] web/app.py — PostHog inicializado")
    else:
        print(f"[WARN] web/app.py — nao encontrei '{marker}', adicione manualmente")


# ─── 4. Verificar requirements.txt ──────────────────────────────────────────
req_path = "requirements.txt"
with open(req_path, "r") as f:
    reqs = f.read()

if "posthog" in reqs:
    print(f"[SKIP] requirements.txt ja tem posthog")
else:
    with open(req_path, "a") as f:
        f.write("\nposthog\n")
    print(f"[OK] requirements.txt — posthog adicionado")


# ─── Resumo ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("PostHog integrado no Prazu!")
print("=" * 50)
print("Proximo passo: faca deploy e acesse qualquer pagina.")
print("Os dados vao aparecer no dashboard do PostHog em ~1 min.")
print("=" * 50)
