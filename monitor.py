import hashlib, json, os, re, sys, urllib.request
from html import escape, unescape

TOPICO = "alerta-fa-veiculos-rafael-2026"
PAGINAS = [
    "https://fundoambiental.pt",
    "https://fundoambiental.pt/apoios-2026/mitigacao-as-alteracoes-climaticas/incentivo-pela-aquisicao-de-veiculos-de-emissoes-nulas-ano-20252026-mobilidade-verde-passageiros-2-fase.aspx",
]
# linhas relevantes: só estas contam para alertas
RELEVANTE = re.compile(
    r"ve[ií]culo|el[eé]tric|mobilidade verde|emiss[oõ]es nulas|candidatura|refor[cç]o|dota[cç][aã]o|incentivo|\b80\s?%",
    re.I)
ESTADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estado.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-PT,pt;q=0.9"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def linhas_relevantes(html):
    html = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>|<!--.*?-->", " ", html)
    html = re.sub(r"(?is)<input[^>]*(__VIEWSTATE\w*|__EVENTVALIDATION|__EVENTTARGET|__EVENTARGUMENT|__PREVIOUSPAGE)[^>]*>", " ", html)
    html = re.sub(r"(?i)</?(p|div|li|tr|td|h\d|br|section|article|a)\b[^>]*>", "\n", html)
    texto = unescape(re.sub(r"<[^>]+>", " ", html))
    out = []
    for l in texto.split("\n"):
        l = re.sub(r"\s+", " ", l).strip()
        if 15 <= len(l) <= 400 and RELEVANTE.search(l) and l not in out:
            out.append(l)
    return out


def notificar(titulo, corpo, link):
    req = urllib.request.Request(
        "https://ntfy.sh/" + TOPICO, data=corpo.encode("utf-8"), method="POST",
        headers={"Title": titulo, "Priority": "urgent", "Tags": "rotating_light,car",
                 "Click": link})  # titulo em ASCII: headers HTTP nao suportam UTF-8
    erros = []
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        erros.append("ntfy " + type(e).__name__)
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat:
        texto = "<b>%s</b>\n%s\n%s" % (escape(titulo), escape(corpo), escape(link))
        tg = urllib.request.Request(
            "https://api.telegram.org/bot%s/sendMessage" % token, method="POST",
            data=json.dumps({"chat_id": chat, "text": texto, "parse_mode": "HTML"}).encode(),
            headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(tg, timeout=30).read()
        except Exception as e:  # nao imprimir e: o URL leva o token
            erros.append("telegram " + type(e).__name__)
    if erros:
        print("falha no envio:", ", ".join(erros))  # sem raise: evita repetir o alerta a cada 5 min


def main():
    if "--teste" in sys.argv:
        notificar("Teste Fundo Ambiental", "Monitor a funcionar. Alerta de teste.", PAGINAS[0])
        print("teste enviado")
        return
    try:
        estado = json.load(open(ESTADO, encoding="utf-8"))
    except (OSError, ValueError):
        estado = {}
    primeira = not estado
    for url in PAGINAS:
        try:
            linhas = linhas_relevantes(baixar(url))
        except Exception as e:  # pagina em baixo: manter estado anterior, tentar daqui a 5 min
            print("falha", url, e)
            continue
        if not linhas:  # pagina estranha (erro/bloqueio): nao sobrescrever
            print("sem conteudo relevante", url)
            continue
        antigas = estado.get(url, {}).get("linhas", [])
        novas = [l for l in linhas if l not in antigas]
        if novas and not primeira and url in estado:
            notificar("Fundo Ambiental: novidade veiculos", "\n".join(novas[:5]), url)
            print("alerta enviado", url)
        if novas or url not in estado:
            estado[url] = {"hash": hashlib.sha256("\n".join(linhas).encode()).hexdigest(), "linhas": linhas}
    novo = json.dumps(estado, ensure_ascii=False, indent=1, sort_keys=True)
    try:
        igual = open(ESTADO, encoding="utf-8").read() == novo
    except OSError:
        igual = False
    if not igual:
        open(ESTADO, "w", encoding="utf-8").write(novo)


if __name__ == "__main__":
    main()
