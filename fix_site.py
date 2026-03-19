"""
Diagnostica links quebrados e atualiza a home page do highnet.
Roda direto na pasta do site.

Uso:
  cd ~/Projects/citation-engine/sites/highnet.com.br
  python fix_site.py
"""

import os
import re
from datetime import datetime

SITE_DIR = os.getcwd()
BLOG_DIR = os.path.join(SITE_DIR, "blog")


def find_blog_folders():
    """Lista todas as pastas de artigos que existem em /blog/."""
    folders = []
    if not os.path.exists(BLOG_DIR):
        return folders
    for item in os.listdir(BLOG_DIR):
        item_path = os.path.join(BLOG_DIR, item)
        if os.path.isdir(item_path) and item != "assets":
            has_index = os.path.exists(os.path.join(item_path, "index.html"))
            folders.append({"slug": item, "has_index": has_index, "path": item_path})
    return folders


def find_internal_links(html_content):
    """Encontra todos os links internos /blog/.../ num HTML."""
    pattern = r'href="/blog/([^"]+?)/"'
    return re.findall(pattern, html_content)


def scan_broken_links():
    """Varre todos os HTMLs e reporta links internos quebrados."""
    existing_slugs = {f["slug"] for f in find_blog_folders()}
    broken = []
    checked = 0

    for root, dirs, files in os.walk(SITE_DIR):
        for fname in files:
            if not fname.endswith(".html"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, "r") as f:
                content = f.read()
            links = find_internal_links(content)
            for link in links:
                checked += 1
                if link not in existing_slugs:
                    rel_path = os.path.relpath(filepath, SITE_DIR)
                    broken.append({"file": rel_path, "link": link})

    return broken, checked


def extract_article_meta(folder_path):
    """Extrai título, descrição, data e tags do HTML de um artigo."""
    index_path = os.path.join(folder_path, "index.html")
    if not os.path.exists(index_path):
        return None

    with open(index_path, "r") as f:
        html = f.read()

    meta = {"slug": os.path.basename(folder_path)}

    # Título
    m = re.search(r'<h1>(.+?)</h1>', html)
    if m:
        meta["title"] = m.group(1)

    # Description
    m = re.search(r'<meta name="description" content="(.+?)"', html)
    if m:
        meta["description"] = m.group(1)

    # Data
    m = re.search(r'article:published_time" content="(.+?)"', html)
    if m:
        meta["date"] = m.group(1)
    else:
        meta["date"] = datetime.now().strftime("%Y-%m-%d")

    # Tags do section-label
    m = re.search(r'section-label">// (.+?)<', html)
    if m:
        meta["tags"] = m.group(1)
    else:
        meta["tags"] = ""

    return meta


def build_home_cards(articles, max_cards=3):
    """Gera HTML dos cards de artigos para a home."""
    sorted_articles = sorted(articles, key=lambda x: x.get("date", ""), reverse=True)

    cards = ""
    for a in sorted_articles[:max_cards]:
        tag = a.get("tags", "").split(" · ")[0] if a.get("tags") else ""
        cards += f'''
      <a href="/blog/{a['slug']}/" class="card">
        <div class="card-tag">{tag}</div>
        <h3>{a.get('title', '')}</h3>
        <p>{a.get('description', '')}</p>
        <div class="card-meta">
          <span>Elio Picchiotti</span>
          <span>{a.get('date', '')}</span>
        </div>
      </a>'''
    return cards


def update_home_page(articles):
    """Atualiza index.html da home com os últimos artigos."""
    home_path = os.path.join(SITE_DIR, "index.html")
    if not os.path.exists(home_path):
        print("  ⚠️ index.html não encontrado")
        return False

    with open(home_path, "r") as f:
        html = f.read()

    cards_html = build_home_cards(articles)

    # Substituir o conteúdo do card-grid
    pattern = r'(<div class="card-grid">)(.*?)(</div>\s*</section>)'
    replacement = f'\\1{cards_html}\n    \\3'

    new_html, count = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)

    if count == 0:
        print("  ⚠️ Não encontrou o card-grid na home para atualizar")
        return False

    with open(home_path, "w") as f:
        f.write(new_html)

    return True


def update_blog_listing(articles):
    """Regenera blog/index.html com listagem atualizada."""
    sorted_articles = sorted(articles, key=lambda x: x.get("date", ""), reverse=True)

    items_html = ""
    for a in sorted_articles:
        items_html += f'''
      <a href="/blog/{a['slug']}/" class="blog-item">
        <div>
          <h3>{a.get('title', '')}</h3>
          <p>{a.get('description', '')}</p>
        </div>
        <time>{a.get('date', '')}</time>
      </a>'''

    listing_html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — HighNet</title>
  <meta name="description" content="Artigos sobre tecnologia, inteligência artificial, negócios digitais e o futuro da informação.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://highnet.com.br/blog/">
  <meta property="og:title" content="Blog — HighNet">
  <meta property="og:description" content="Artigos aprofundados sobre tecnologia, IA e negócios digitais.">
  <meta property="og:url" content="https://highnet.com.br/blog/">
  <meta property="og:type" content="website">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/style.css">
  <link rel="icon" href="/favicon.ico">
</head>
<body>

  <header class="site-header">
    <div class="header-inner">
      <a href="/" class="logo">high<span>net</span></a>
      <button class="nav-toggle" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
      <nav>
        <a href="/">Home</a>
        <a href="/blog/" class="active">Blog</a>
        <a href="/sobre.html">Sobre</a>
        <a href="/contato.html">Contato</a>
      </nav>
    </div>
  </header>

  <section class="section">
    <div class="section-label">// publicações</div>
    <h2>Blog</h2>
    <p class="section-desc">Análises aprofundadas sobre tecnologia, IA e negócios digitais. Artigos longos, com dados e fontes verificáveis.</p>

    <div class="blog-list">
{items_html}
    </div>
  </section>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="logo">high<span>net</span></div>
          <p>Editorial independente sobre tecnologia, IA e negócios digitais.</p>
        </div>
        <div class="footer-col">
          <h4>Navegação</h4>
          <a href="/">Home</a>
          <a href="/blog/">Blog</a>
          <a href="/sobre.html">Sobre</a>
          <a href="/contato.html">Contato</a>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <a href="/privacidade.html">Política de privacidade</a>
          <a href="/sobre.html">Equipe editorial</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 HighNet. Todos os direitos reservados.</span>
        <span>highnet.com.br</span>
      </div>
    </div>
  </footer>

  <script src="/assets/js/main.js"></script>
</body>
</html>'''

    listing_path = os.path.join(BLOG_DIR, "index.html")
    with open(listing_path, "w") as f:
        f.write(listing_html)

    return True


def main():
    print("🔍 Diagnosticando highnet.com.br...")
    print()

    # 1. Listar artigos existentes
    folders = find_blog_folders()
    print(f"📂 Artigos encontrados em /blog/: {len(folders)}")
    for f in sorted(folders, key=lambda x: x["slug"]):
        status = "✅" if f["has_index"] else "❌ (sem index.html!)"
        print(f"   {status} /blog/{f['slug']}/")
    print()

    # 2. Checar links quebrados
    broken, total = scan_broken_links()
    if broken:
        print(f"🔗 Links internos: {total} verificados, {len(broken)} QUEBRADOS:")
        for b in broken:
            print(f"   ❌ {b['file']} → /blog/{b['link']}/")

        # Mostrar slugs disponíveis pra ajudar a corrigir
        existing = {f["slug"] for f in folders}
        broken_slugs = {b["link"] for b in broken}
        print()
        print("   Slugs que existem:")
        for s in sorted(existing):
            print(f"     ✅ {s}")
        print()
        print("   Slugs nos links que NÃO existem:")
        for s in sorted(broken_slugs):
            # Tentar achar o mais parecido
            candidates = [e for e in existing if s[:15] in e or e[:15] in s]
            hint = f" → talvez seja: {candidates[0]}" if candidates else ""
            print(f"     ❌ {s}{hint}")
    else:
        print(f"🔗 Links internos: {total} verificados, todos OK ✅")
    print()

    # 3. Extrair meta de todos os artigos
    articles = []
    for f in folders:
        if f["has_index"]:
            meta = extract_article_meta(f["path"])
            if meta:
                articles.append(meta)

    # 4. Atualizar home page
    print("🏠 Atualizando home page...")
    if update_home_page(articles):
        print("   ✅ index.html atualizado com últimos 3 artigos")
    print()

    # 5. Atualizar blog listing
    print("📋 Atualizando blog/index.html...")
    if update_blog_listing(articles):
        print(f"   ✅ Listagem atualizada com {len(articles)} artigos")
    print()

    print("=" * 50)
    print("Próximo passo:")
    print("  git add .")
    print('  git commit -m "fix: atualizar home + corrigir links"')
    print("  git push")


if __name__ == "__main__":
    main()
