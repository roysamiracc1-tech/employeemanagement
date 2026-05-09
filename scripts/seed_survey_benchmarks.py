"""Seed Stack Overflow Developer Survey 2025 benchmark data.

Run once:  python3 scripts/seed_survey_benchmarks.py
Safe to re-run (UPSERT).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from app.db import execute

# ── Survey data ───────────────────────────────────────────────────────────────
SOURCE = 'Stack Overflow Developer Survey'
YEAR   = 2025
URL    = 'https://survey.stackoverflow.co/2025'

SURVEY_DATA = {
    'Programming Languages': [
        ('JavaScript',          66.0),
        ('HTML/CSS',            61.9),
        ('SQL',                 58.6),
        ('Python',              57.9),
        ('Bash/Shell',          48.7),
        ('TypeScript',          43.6),
        ('Java',                29.4),
        ('C#',                  27.8),
        ('C++',                 23.5),
        ('PowerShell',          23.2),
        ('C',                   22.0),
        ('PHP',                 18.9),
        ('Go',                  16.4),
        ('Rust',                14.8),
        ('Kotlin',              10.8),
        ('Lua',                  9.2),
        ('Assembly',             7.1),
        ('Ruby',                 6.4),
        ('Dart',                 5.9),
        ('Swift',                5.4),
        ('R',                    4.9),
        ('Groovy',               4.8),
        ('Visual Basic (.Net)',  4.4),
        ('VBA',                  4.2),
        ('MATLAB',               3.9),
        ('Perl',                 3.8),
        ('GDScript',             3.3),
        ('Elixir',               2.7),
        ('Scala',                2.6),
        ('Delphi',               2.5),
        ('Lisp',                 2.4),
        ('MicroPython',          2.3),
        ('Zig',                  2.1),
        ('Erlang',               1.5),
        ('Fortran',              1.4),
        ('Ada',                  1.4),
        ('F#',                   1.3),
        ('OCaml',                1.2),
        ('Gleam',                1.1),
        ('Prolog',               1.1),
        ('COBOL',                1.0),
        ('Mojo',                 0.4),
    ],
    'Databases': [
        ('PostgreSQL',              55.6),
        ('MySQL',                   40.5),
        ('SQLite',                  37.5),
        ('Microsoft SQL Server',    30.1),
        ('Redis',                   28.0),
        ('MongoDB',                 24.0),
        ('MariaDB',                 22.5),
        ('Elasticsearch',           16.7),
        ('Oracle',                  10.6),
        ('DynamoDB',                 9.8),
        ('BigQuery',                 6.5),
        ('Supabase',                 6.0),
        ('Cloud Firestore',          5.7),
        ('H2',                       5.0),
        ('Firebase Realtime DB',     5.0),
        ('Microsoft Access',         4.8),
        ('Cosmos DB',                4.6),
        ('Snowflake',                4.1),
        ('InfluxDB',                 3.7),
        ('Databricks SQL',           3.4),
        ('DuckDB',                   3.3),
        ('Cassandra',                2.9),
        ('Neo4J',                    2.6),
        ('Valkey',                   2.4),
        ('ClickHouse',               2.4),
        ('IBM DB2',                  2.4),
        ('Amazon Redshift',          2.3),
        ('CockroachDB',              1.0),
        ('Pocketbase',               1.0),
        ('Datomic',                  0.6),
    ],
    'Web Frameworks': [
        ('Node.js',         48.7),
        ('React',           44.7),
        ('jQuery',          23.4),
        ('Next.js',         20.8),
        ('Express',         19.9),
        ('ASP.NET Core',    19.7),
        ('Angular',         18.2),
        ('Vue.js',          17.6),
        ('FastAPI',         14.8),
        ('Spring Boot',     14.7),
        ('Flask',           14.4),
        ('ASP.NET',         14.2),
        ('WordPress',       13.6),
        ('Django',          12.6),
        ('Laravel',          8.9),
        ('AngularJS',        7.2),
        ('Svelte',           7.2),
        ('Blazor',           7.0),
        ('NestJS',           6.7),
        ('Ruby on Rails',    5.9),
        ('Astro',            4.5),
        ('Deno',             4.0),
        ('Symfony',          4.0),
        ('Nuxt.js',          4.0),
        ('Fastify',          2.9),
        ('Axum',             2.8),
        ('Phoenix',          2.4),
        ('Drupal',           2.2),
    ],
    'Cloud & DevOps': [
        ('Docker',          71.1),
        ('npm',             56.8),
        ('AWS',             43.3),
        ('Pip',             40.9),
        ('Kubernetes',      28.5),
        ('Azure',           26.3),
        ('Homebrew',        25.7),
        ('Vite',            25.4),
        ('Google Cloud',    24.6),
        ('Make',            23.2),
        ('Yarn',            21.1),
        ('Cloudflare',      20.1),
        ('NuGet',           18.9),
        ('APT',             18.4),
        ('Webpack',         18.4),
        ('Terraform',       17.8),
        ('Maven',           16.4),
        ('Cargo',           14.4),
        ('Gradle',          14.4),
        ('pnpm',            13.4),
        ('Firebase',        13.1),
        ('Prometheus',      11.8),
        ('Ansible',         11.7),
        ('Podman',          11.1),
        ('Chocolatey',      11.0),
        ('Composer',        11.0),
        ('MSBuild',         11.0),
        ('Digital Ocean',   10.7),
        ('Vercel',          10.6),
        ('Poetry',           9.0),
        ('Datadog',          8.9),
        ('Pacman',           8.7),
        ('Netlify',          5.9),
        ('Bun',              5.5),
        ('Supabase',         5.4),
        ('Heroku',           5.4),
        ('Splunk',           4.5),
        ('New Relic',        3.8),
        ('Railway',          1.5),
        ('IBM Cloud',        1.2),
        ('Yandex Cloud',     0.7),
    ],
    'Dev IDEs': [
        ('Visual Studio Code',      75.9),
        ('Visual Studio',           29.0),
        ('Notepad++',               27.4),
        ('IntelliJ IDEA',           27.1),
        ('Vim',                     24.3),
        ('Cursor',                  17.9),
        ('PyCharm',                 15.0),
        ('Android Studio',          15.0),
        ('Jupyter Nb/JupyterLab',   14.1),
        ('Neovim',                  14.0),
        ('Nano',                    12.2),
        ('Sublime Text',            10.5),
        ('Xcode',                   10.0),
        ('Claude Code',              9.7),
        ('WebStorm',                 7.6),
        ('Zed',                      7.3),
        ('Rider',                    7.1),
        ('Eclipse',                  7.1),
        ('VSCodium',                 6.2),
        ('PhpStorm',                 5.8),
        ('Windsurf',                 4.9),
        ('RustRover',                3.2),
        ('Lovable.dev',              2.4),
        ('Bolt',                     2.3),
        ('Cline / Roo',              2.2),
        ('Aider',                    1.9),
        ('Trae',                     0.8),
    ],
    'Large Language Models': [
        ('OpenAI GPT',          81.4),
        ('Claude Sonnet',       42.8),
        ('Gemini Flash',        35.3),
        ('OpenAI Reasoning',    34.6),
        ('OpenAI Image',        26.6),
        ('Gemini Reasoning',    25.6),
        ('DeepSeek Reasoning',  23.3),
        ('Meta Llama',          17.8),
        ('DeepSeek General',    14.3),
        ('X Grok',              11.1),
        ('Mistral',             10.4),
        ('Perplexity Sonar',     7.6),
        ('Alibaba Qwen',         5.2),
        ('Microsoft Phi-4',      5.0),
        ('Amazon Titan',         1.7),
        ('Cohere Command A',     0.8),
        ('Reka',                 0.4),
    ],
    'Collaboration Tools': [
        ('GitHub',                  81.1),
        ('Jira',                    46.4),
        ('GitLab',                  35.6),
        ('Markdown File',           34.8),
        ('Confluence',              32.8),
        ('Azure DevOps',            16.6),
        ('Notion',                  16.5),
        ('Obsidian',                16.1),
        ('Google Workspace',        15.2),
        ('Miro',                    14.3),
        ('Trello',                  13.7),
        ('Wikis',                   10.4),
        ('Google Colab',             7.0),
        ('Lucid / Lucidchart',       5.3),
        ('Asana',                    4.4),
        ('Doxygen',                  4.3),
        ('Clickup',                  3.9),
        ('Linear',                   3.7),
        ('Microsoft Planner',        2.9),
        ('Monday.com',               2.6),
        ('Redmine',                  2.5),
        ('Airtable',                 2.5),
        ('YouTrack',                 2.4),
        ('Stack Overflow for Teams', 2.4),
        ('Coda',                     1.0),
    ],
    'Community Platforms': [
        ('Stack Overflow',   84.2),
        ('GitHub (public)',  66.9),
        ('YouTube',          60.5),
        ('Reddit',           53.7),
        ('Stack Exchange',   46.5),
        ('Discord',          38.9),
        ('LinkedIn',         37.2),
        ('Medium',           29.3),
        ('Hacker News',      19.6),
        ('X (Twitter)',      17.1),
        ('Slack (public)',   15.7),
        ('Dev.to',           11.5),
        ('Bluesky',          10.8),
        ('Twitch',            8.9),
        ('Substack',          7.1),
        ('Company forum',     6.2),
        ('Kaggle',            4.3),
        ('Hashnode',          1.2),
    ],
    'Trending Topics': [
        ('Google Gemini',       29.2),
        ('Large language model', 27.6),
        ('Tailwind CSS 4',      21.8),
        ('.NET 8+',             19.2),
        ('Ollama',              15.3),
        ('RAG',                 10.6),
        ('Pydantic',            10.1),
        ('uv',                   9.5),
        ('Shadcn/ui',            8.7),
        ('C++23',                7.3),
        ('Amazon Bedrock',       4.7),
        ('Polars',               3.8),
        ('LangGraph',            3.0),
        ('Microsoft Fabric',     2.4),
        ('Odoo',                 2.1),
        ('SwiftData',            1.7),
        ('Ultralytics',          1.2),
        ('visionOS',             0.9),
    ],
}

# Operating systems handled separately (personal + professional context)
OS_DATA = [
    ('Windows',                 56.7, 'personal'),
    ('Windows',                 49.5, 'professional'),
    ('MacOS',                   32.7, 'personal'),
    ('MacOS',                   32.9, 'professional'),
    ('Android',                 29.1, 'personal'),
    ('Android',                 11.9, 'professional'),
    ('Ubuntu',                  27.8, 'personal'),
    ('Ubuntu',                  27.7, 'professional'),
    ('iOS',                     18.9, 'personal'),
    ('iOS',                     10.5, 'professional'),
    ('Linux (non-WSL)',          17.6, 'personal'),
    ('Linux (non-WSL)',          16.7, 'professional'),
    ('WSL',                     15.9, 'personal'),
    ('WSL',                     16.8, 'professional'),
    ('Debian',                  11.4, 'personal'),
    ('Debian',                  10.4, 'professional'),
    ('Arch',                     9.7, 'personal'),
    ('Arch',                     4.6, 'professional'),
    ('iPadOS',                   8.1, 'personal'),
    ('iPadOS',                   2.8, 'professional'),
    ('Fedora',                   5.8, 'personal'),
    ('Fedora',                   3.7, 'professional'),
    ('Red Hat',                  1.8, 'personal'),
    ('Red Hat',                  5.7, 'professional'),
    ('NixOS',                    3.4, 'personal'),
    ('NixOS',                    1.8, 'professional'),
    ('Pop!_OS',                  2.3, 'personal'),
    ('Pop!_OS',                  1.1, 'professional'),
    ('ChromeOS',                 2.3, 'personal'),
    ('ChromeOS',                 1.2, 'professional'),
]


def run():
    with app.app_context():
        # Create table
        execute("""
            CREATE TABLE IF NOT EXISTS survey_benchmarks (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                survey_source   VARCHAR(100) NOT NULL,
                survey_year     SMALLINT NOT NULL,
                category        VARCHAR(100) NOT NULL,
                technology      VARCHAR(200) NOT NULL,
                usage_pct       NUMERIC(5,1) NOT NULL,
                context         VARCHAR(50) NOT NULL DEFAULT 'all_respondents',
                rank_in_category SMALLINT,
                source_url      TEXT,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (survey_source, survey_year, category, technology, context)
            )
        """)
        execute("""CREATE INDEX IF NOT EXISTS idx_sb_category_year
                   ON survey_benchmarks(survey_year, category)""")

        inserted = 0

        # Main categories
        for category, items in SURVEY_DATA.items():
            for rank, (tech, pct) in enumerate(items, 1):
                execute("""
                    INSERT INTO survey_benchmarks
                        (survey_source, survey_year, category, technology,
                         usage_pct, context, rank_in_category, source_url)
                    VALUES (%s, %s, %s, %s, %s, 'all_respondents', %s, %s)
                    ON CONFLICT (survey_source, survey_year, category, technology, context)
                    DO UPDATE SET usage_pct = EXCLUDED.usage_pct,
                                  rank_in_category = EXCLUDED.rank_in_category
                """, (SOURCE, YEAR, category, tech, pct, rank, URL))
                inserted += 1

        # Operating systems (two contexts)
        seen_rank = {}
        for tech, pct, ctx in OS_DATA:
            key = (tech, ctx)
            rank = seen_rank.get(ctx, 0) + 1
            seen_rank[ctx] = rank
            execute("""
                INSERT INTO survey_benchmarks
                    (survey_source, survey_year, category, technology,
                     usage_pct, context, rank_in_category, source_url)
                VALUES (%s, %s, 'Operating Systems', %s, %s, %s, %s, %s)
                ON CONFLICT (survey_source, survey_year, category, technology, context)
                DO UPDATE SET usage_pct = EXCLUDED.usage_pct,
                              rank_in_category = EXCLUDED.rank_in_category
            """, (SOURCE, YEAR, tech, pct, ctx, rank, URL))
            inserted += 1

        print(f'Seeded {inserted} benchmark rows for SO {YEAR}.')


if __name__ == '__main__':
    run()
