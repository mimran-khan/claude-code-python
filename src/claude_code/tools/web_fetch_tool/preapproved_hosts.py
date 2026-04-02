"""Preapproved WebFetch host allowlist. Migrated from tools/WebFetchTool/preapproved.ts"""

PREAPPROVED_HOSTS: frozenset[str] = frozenset(
    {
        "platform.claude.com",
        "code.claude.com",
        "modelcontextprotocol.io",
        "github.com/anthropics",
        "agentskills.io",
        "docs.python.org",
        "en.cppreference.com",
        "docs.oracle.com",
        "learn.microsoft.com",
        "developer.mozilla.org",
        "go.dev",
        "pkg.go.dev",
        "www.php.net",
        "docs.swift.org",
        "kotlinlang.org",
        "ruby-doc.org",
        "doc.rust-lang.org",
        "www.typescriptlang.org",
        "react.dev",
        "angular.io",
        "vuejs.org",
        "nextjs.org",
        "expressjs.com",
        "nodejs.org",
        "bun.sh",
        "jquery.com",
        "getbootstrap.com",
        "tailwindcss.com",
        "d3js.org",
        "threejs.org",
        "redux.js.org",
        "webpack.js.org",
        "jestjs.io",
        "reactrouter.com",
        "docs.djangoproject.com",
        "flask.palletsprojects.com",
        "fastapi.tiangolo.com",
        "pandas.pydata.org",
        "numpy.org",
        "www.tensorflow.org",
        "pytorch.org",
        "scikit-learn.org",
        "matplotlib.org",
        "requests.readthedocs.io",
        "jupyter.org",
        "laravel.com",
        "symfony.com",
        "wordpress.org",
        "docs.spring.io",
        "hibernate.org",
        "tomcat.apache.org",
        "gradle.org",
        "maven.apache.org",
        "asp.net",
        "dotnet.microsoft.com",
        "nuget.org",
        "blazor.net",
        "reactnative.dev",
        "docs.flutter.dev",
        "developer.apple.com",
        "developer.android.com",
        "keras.io",
        "spark.apache.org",
        "huggingface.co",
        "www.kaggle.com",
        "www.mongodb.com",
        "redis.io",
        "www.postgresql.org",
        "dev.mysql.com",
        "www.sqlite.org",
        "graphql.org",
        "prisma.io",
        "docs.aws.amazon.com",
        "cloud.google.com",
        "kubernetes.io",
        "www.docker.com",
        "www.terraform.io",
        "www.ansible.com",
        "vercel.com/docs",
        "docs.netlify.com",
        "devcenter.heroku.com",
        "cypress.io",
        "selenium.dev",
        "docs.unity.com",
        "docs.unrealengine.com",
        "git-scm.com",
        "nginx.org",
        "httpd.apache.org",
    }
)


def _split_preapproved_entries() -> tuple[frozenset[str], dict[str, tuple[str, ...]]]:
    hostname_only: set[str] = set()
    path_prefixes: dict[str, list[str]] = {}
    for entry in PREAPPROVED_HOSTS:
        if "/" not in entry:
            hostname_only.add(entry)
            continue
        host, _, rest = entry.partition("/")
        path = "/" + rest if rest else ""
        path_prefixes.setdefault(host, []).append(path)
    frozen_paths = {h: tuple(p) for h, p in path_prefixes.items()}
    return frozenset(hostname_only), frozen_paths


_HOSTNAME_ONLY, _PATH_PREFIXES = _split_preapproved_entries()


def is_preapproved_host(hostname: str, pathname: str) -> bool:
    """Return True if the host/path is on the WebFetch preapproved allowlist (TS parity)."""
    if hostname in _HOSTNAME_ONLY:
        return True
    prefixes = _PATH_PREFIXES.get(hostname)
    if not prefixes:
        return False
    return any(pathname == prefix or pathname.startswith(prefix + "/") for prefix in prefixes)
