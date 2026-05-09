"""Seed Stack Overflow Developer Survey 2025 — Admired & Desired data.

Desired  = % of ALL respondents who want to use the technology next year
           (but don't currently use it — "wish list")
Admired  = % of users who HAVE used the technology in the past year
           and want to CONTINUE using it ("love / satisfaction rate")

Gap (admired − desired) gauges hype vs reality:
  Large positive gap → under-hyped gem (loved by users, less known)
  Small gap          → mainstream / broadly wanted and broadly liked

Run:  python3 scripts/seed_survey_admired_desired.py
Safe to re-run (UPSERT).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from app.db import execute

SOURCE = 'Stack Overflow Developer Survey'
YEAR   = 2025
URL    = 'https://survey.stackoverflow.co/2025'

# Each entry: (technology, desired_pct, admired_pct)
ADMIRED_DESIRED = {

    'Programming Languages': [
        ('Python',              39.3, 56.4),
        ('SQL',                 35.6, 56.4),
        ('HTML/CSS',            33.8, 52.1),
        ('JavaScript',          33.5, 46.8),
        ('TypeScript',          31.9, 58.0),
        ('Rust',                29.2, 72.4),
        ('Bash/Shell',          27.4, 52.8),
        ('Go',                  23.4, 56.5),
        ('C#',                  19.4, 55.8),
        ('C++',                 16.7, 46.6),
        ('Java',                15.8, 41.8),
        ('C',                   14.5, 45.0),
        ('Kotlin',              12.0, 51.0),
        ('PowerShell',           9.6, 35.4),
        ('PHP',                  9.2, 38.9),
        ('Zig',                  7.7, 64.2),
        ('Lua',                  7.6, 46.9),
        ('Assembly',             6.9, 45.3),
        ('Swift',                6.5, 51.9),
        ('Elixir',               5.8, 65.9),
        ('Dart',                 5.3, 47.0),
        ('Ruby',                 5.1, 44.3),
        ('R',                    4.2, 39.6),
        ('Lisp',                 3.6, 57.9),
        ('GDScript',             3.4, 56.9),
        ('Gleam',                3.1, 70.8),
        ('Erlang',               3.1, 50.0),
        ('Scala',                3.0, 39.4),
        ('F#',                   2.9, 49.1),
        ('OCaml',                2.8, 51.5),
        ('MicroPython',          2.7, 44.4),
        ('Perl',                 2.3, 32.5),
        ('MATLAB',               2.0, 24.0),
        ('Groovy',               2.0, 25.9),
        ('Visual Basic (.Net)',  1.9, 24.5),
        ('Mojo',                 1.9, 49.3),
        ('Delphi',               1.9, 46.0),
        ('Ada',                  1.8, 41.2),
        ('VBA',                  1.6, 24.5),
        ('Prolog',               1.4, 32.6),
        ('COBOL',                1.4, 28.2),
        ('Fortran',              1.3, 29.0),
    ],

    'Databases': [
        ('PostgreSQL',              46.5, 65.5),
        ('SQLite',                  28.3, 59.0),
        ('Redis',                   23.5, 54.9),
        ('MySQL',                   20.5, 43.2),
        ('MongoDB',                 17.6, 45.7),
        ('Microsoft SQL Server',    15.2, 44.9),
        ('Elasticsearch',           12.9, 39.4),
        ('MariaDB',                 12.8, 45.8),
        ('DynamoDB',                 6.9, 39.7),
        ('Supabase',                 6.4, 47.2),
        ('DuckDB',                   5.7, 58.8),
        ('BigQuery',                 5.6, 38.9),
        ('Oracle',                   5.2, 32.0),
        ('Valkey',                   4.9, 64.7),
        ('Cassandra',                4.9, 31.8),
        ('Snowflake',                4.3, 39.6),
        ('Firebase Realtime DB',     4.2, 35.9),
        ('Cosmos DB',                4.0, 38.1),
        ('Cloud Firestore',          4.0, 40.1),
        ('Neo4J',                    3.9, 41.7),
        ('Databricks SQL',           3.7, 40.5),
        ('ClickHouse',               3.4, 48.1),
        ('InfluxDB',                 2.9, 38.1),
        ('Amazon Redshift',          2.8, 31.6),
        ('CockroachDB',              2.6, 37.0),
        ('H2',                       2.5, 34.8),
        ('Pocketbase',               1.7, 49.2),
        ('Microsoft Access',         1.7, 21.9),
        ('IBM DB2',                  1.5, 29.0),
        ('Datomic',                  1.2, 43.9),
    ],

    'Web Frameworks': [
        ('React',           30.7, 52.1),
        ('Node.js',         29.7, 52.2),
        ('Vue.js',          15.3, 50.9),
        ('Next.js',         14.9, 45.5),
        ('ASP.NET Core',    14.7, 61.3),
        ('FastAPI',         13.0, 55.5),
        ('Angular',         12.6, 44.7),
        ('Express',         11.4, 45.5),
        ('Svelte',          11.1, 62.4),
        ('Spring Boot',     11.0, 53.7),
        ('Django',          10.4, 46.4),
        ('jQuery',           9.0, 31.4),
        ('Flask',            8.9, 41.7),
        ('Blazor',           7.1, 51.9),
        ('Laravel',          6.5, 47.8),
        ('Deno',             6.5, 52.1),
        ('ASP.NET',          6.5, 34.1),
        ('NestJS',           6.0, 49.8),
        ('Astro',            5.9, 62.2),
        ('WordPress',        5.7, 30.4),
        ('Ruby on Rails',    5.5, 52.0),
        ('Nuxt.js',          4.0, 46.4),
        ('AngularJS',        4.0, 21.9),
        ('Phoenix',          4.0, 79.0),
        ('Axum',             3.8, 76.4),
        ('Symfony',          3.1, 50.0),
        ('Fastify',          2.7, 49.7),
        ('Drupal',           1.4, 33.7),
    ],

    'Cloud & DevOps': [
        ('Docker',          50.4, 63.6),
        ('AWS',             29.5, 51.9),
        ('Kubernetes',      27.9, 58.0),
        ('npm',             26.8, 45.0),
        ('Pip',             19.5, 45.0),
        ('Vite',            18.3, 61.1),
        ('Azure',           17.0, 49.6),
        ('Google Cloud',    16.7, 46.1),
        ('Cloudflare',      16.0, 57.5),
        ('Terraform',       15.7, 51.8),
        ('Homebrew',        15.2, 56.4),
        ('Cargo',           13.9, 70.8),
        ('Make',            12.6, 47.6),
        ('APT',             11.5, 58.8),
        ('NuGet',           11.0, 53.8),
        ('Podman',          10.3, 57.4),
        ('Prometheus',       9.9, 54.7),
        ('Ansible',          9.8, 49.6),
        ('pnpm',             9.3, 53.9),
        ('Firebase',         9.1, 45.4),
        ('Yarn',             8.8, 34.8),
        ('Maven',            8.2, 43.5),
        ('Gradle',           7.5, 42.1),
        ('Digital Ocean',    7.5, 46.9),
        ('Vercel',           6.8, 44.4),
        ('Composer',         6.4, 49.0),
        ('Pacman',           6.3, 63.0),
        ('Bun',              6.2, 55.8),
        ('Datadog',          6.0, 43.8),
        ('Webpack',          5.9, 25.7),
        ('MSBuild',          5.9, 46.9),
        ('Supabase',         5.4, 50.9),
        ('Chocolatey',       5.0, 35.0),
        ('Poetry',           4.5, 35.4),
        ('Netlify',          3.9, 45.0),
        ('Ninja',            3.6, 50.8),
        ('Heroku',           3.0, 26.6),
        ('Splunk',           2.7, 35.0),
        ('New Relic',        2.3, 37.5),
        ('IBM Cloud',        1.6, 38.4),
        ('Railway',          1.5, 47.1),
        ('Yandex Cloud',     0.9, 48.5),
    ],

    'Dev IDEs': [
        ('Visual Studio Code',      48.9, 62.6),
        ('IntelliJ IDEA',           17.5, 58.2),
        ('Visual Studio',           16.0, 51.8),
        ('Vim',                     15.7, 59.3),
        ('Notepad++',               15.5, 54.7),
        ('Cursor',                  14.6, 46.7),
        ('Neovim',                  13.3, 74.4),
        ('Claude Code',             10.3, 52.5),
        ('PyCharm',                  9.6, 52.9),
        ('Jupyter Nb/JupyterLab',    9.3, 53.8),
        ('Android Studio',           8.8, 43.2),
        ('Zed',                      7.5, 57.0),
        ('Nano',                     6.7, 51.2),
        ('Xcode',                    6.1, 41.3),
        ('Sublime Text',             5.9, 50.1),
        ('WebStorm',                 5.7, 59.1),
        ('Rider',                    5.6, 60.8),
        ('VSCodium',                 5.0, 56.7),
        ('Windsurf',                 4.3, 41.8),
        ('PhpStorm',                 3.8, 53.8),
        ('RustRover',                3.7, 62.6),
        ('Eclipse',                  3.0, 32.9),
        ('Lovable.dev',              1.9, 36.6),
        ('Cline / Roo',              1.8, 44.8),
        ('Aider',                    1.8, 43.9),
        ('Bolt',                     1.6, 36.4),
        ('Trae',                     0.8, 41.5),
    ],

    'Large Language Models': [
        ('OpenAI GPT',          51.2, 61.2),
        ('Claude Sonnet',       33.3, 67.5),
        ('OpenAI Reasoning',    25.9, 63.6),
        ('Gemini Flash',        24.0, 56.6),
        ('Gemini Reasoning',    22.7, 65.2),
        ('OpenAI Image',        18.7, 59.4),
        ('DeepSeek Reasoning',  17.1, 51.5),
        ('Meta Llama',          12.5, 48.3),
        ('DeepSeek General',    11.4, 51.2),
        ('X Grok',               8.9, 52.0),
        ('Mistral',              8.0, 49.6),
        ('Perplexity Sonar',     6.3, 54.7),
        ('Alibaba Qwen',         4.3, 53.8),
        ('Microsoft Phi-4',      4.0, 42.6),
        ('Amazon Titan',         2.1, 42.9),
        ('Cohere Command A',     1.1, 41.7),
        ('Reka',                 0.9, 61.4),
    ],

    'Collaboration Tools': [
        ('GitHub',                  59.3, 70.1),
        ('Markdown File',           27.0, 75.8),
        ('GitLab',                  25.6, 59.5),
        ('Jira',                    22.0, 42.1),
        ('Confluence',              14.3, 40.2),
        ('Obsidian',                13.8, 66.6),
        ('Azure DevOps',             9.9, 49.1),
        ('Notion',                   9.7, 46.1),
        ('Google Workspace',         9.5, 54.3),
        ('Wikis',                    7.5, 63.4),
        ('Trello',                   6.8, 38.4),
        ('Miro',                     6.4, 38.6),
        ('Google Colab',             4.9, 50.3),
        ('Linear',                   3.6, 58.8),
        ('Doxygen',                  3.0, 49.6),
        ('Lucid / Lucidchart',       2.7, 42.3),
        ('Stack Overflow for Teams', 2.6, 46.3),
        ('Asana',                    2.0, 30.5),
        ('Clickup',                  2.0, 33.0),
        ('YouTrack',                 1.9, 46.7),
        ('Microsoft Planner',        1.5, 33.9),
        ('Airtable',                 1.5, 29.9),
        ('Redmine',                  1.5, 40.5),
        ('Monday.com',               1.2, 22.3),
        ('Coda',                     0.8, 35.0),
    ],

    'Community Platforms': [
        ('Stack Overflow',   60.9, 70.7),
        ('GitHub (public)',  50.5, 72.4),
        ('YouTube',          42.1, 68.4),
        ('Stack Exchange',   34.4, 71.4),
        ('Reddit',           32.8, 59.0),
        ('Discord',          25.6, 60.7),
        ('LinkedIn',         20.7, 52.3),
        ('Medium',           15.4, 49.6),
        ('Hacker News',      14.2, 63.3),
        ('Slack (public)',   10.0, 54.0),
        ('Bluesky',           9.1, 65.7),
        ('X (Twitter)',       8.9, 47.7),
        ('Dev.to',            7.5, 55.3),
        ('Twitch',            6.3, 59.3),
        ('Substack',          4.8, 54.0),
        ('Company forum',     4.0, 56.1),
        ('Kaggle',            3.9, 56.5),
        ('Hashnode',          1.1, 52.9),
    ],

    'Trending Topics': [
        ('Large language model', 27.3, 67.6),
        ('Google Gemini',        24.9, 58.9),
        ('Tailwind CSS 4',       22.1, 62.1),
        ('.NET 8+',              16.7, 67.1),
        ('Ollama',               15.4, 59.9),
        ('RAG',                  13.9, 61.4),
        ('C++23',                12.4, 65.1),
        ('uv',                   11.3, 74.2),
        ('Shadcn/ui',             9.4, 62.6),
        ('Pydantic',              9.2, 61.2),
        ('Polars',                6.2, 67.9),
        ('Amazon Bedrock',        5.6, 49.2),
        ('LangGraph',             4.6, 51.7),
        ('Microsoft Fabric',      3.8, 46.2),
        ('SwiftData',             2.8, 59.8),
        ('hostinger',             2.7, 45.7),
        ('visionOS',              2.6, 51.9),
        ('Odoo',                  2.6, 39.2),
        ('Delphi 12+ Athens',     2.3, 69.5),
        ('Ultralytics',           1.3, 48.4),
    ],
}


def run():
    with app.app_context():
        total_updated  = 0
        total_inserted = 0

        for category, items in ADMIRED_DESIRED.items():
            for rank, (tech, desired, admired) in enumerate(items, 1):
                # Try to update an existing "all_respondents" row first
                execute("""
                    INSERT INTO survey_benchmarks
                        (survey_source, survey_year, category, technology,
                         usage_pct, context, rank_in_category, source_url,
                         desired_pct, admired_pct)
                    VALUES (%s, %s, %s, %s, 0, 'all_respondents', %s, %s, %s, %s)
                    ON CONFLICT (survey_source, survey_year, category, technology, context)
                    DO UPDATE SET
                        desired_pct      = EXCLUDED.desired_pct,
                        admired_pct      = EXCLUDED.admired_pct,
                        rank_in_category = EXCLUDED.rank_in_category
                """, (SOURCE, YEAR, category, tech, rank, URL, desired, admired))
                total_updated += 1

        print(f'Upserted {total_updated} admired/desired rows for SO {YEAR}.')


if __name__ == '__main__':
    run()
