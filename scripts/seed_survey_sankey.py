"""Seed Stack Overflow Developer Survey 2025 — Worked with vs. Want to work with.

Sankey roles per technology:
  'worked_with'        — Left side: developers currently use this
  'want_to_work_with'  — Right side: developers want to use next year
  'both'               — Central/large: widely used AND widely wanted

Interpretation: if a developer uses a 'worked_with' technology, the flow
shows they desire a 'want_to_work_with' technology. 'both' technologies
are sticky — developers who use them want to keep using them.

Run:  python3 scripts/seed_survey_sankey.py
Safe to re-run (UPSERT).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from app.db import execute

SOURCE = 'Stack Overflow Developer Survey'
YEAR   = 2025

# (technology, sankey_role)
# worked_with   = currently using, looking to transition from / add to
# want_to_work_with = high pull — many developers from different stacks want this
# both          = core/sticky — heavily used AND heavily desired to continue
SANKEY_DATA = {

    'Programming Languages': [
        # Left — currently used "origin" stack
        ('PHP',                 'worked_with'),
        ('PowerShell',          'worked_with'),
        ('JavaScript',          'worked_with'),
        ('HTML/CSS',            'worked_with'),
        ('Java',                'worked_with'),
        ('SQL',                 'worked_with'),
        ('Bash/Shell',          'worked_with'),
        # Both — core / sticky
        ('Python',              'both'),
        ('C#',                  'both'),
        ('C++',                 'both'),
        ('C',                   'both'),
        # Right — high pull / desired destinations
        ('Go',                  'want_to_work_with'),
        ('TypeScript',          'want_to_work_with'),
        ('Rust',                'want_to_work_with'),
        ('Kotlin',              'want_to_work_with'),
    ],

    'Databases': [
        # Left — currently used legacy/relational stack
        ('MariaDB',             'worked_with'),
        ('Microsoft SQL Server','worked_with'),
        ('MongoDB',             'worked_with'),
        ('MySQL',               'worked_with'),
        # Both — widely used and wanted
        ('SQLite',              'both'),
        ('Redis',               'both'),
        # Right — destination of choice
        ('PostgreSQL',          'want_to_work_with'),
    ],

    'Web Frameworks': [
        # Left
        ('Express',             'worked_with'),
        # Both — core / sticky
        ('Node.js',             'both'),
        ('React',               'both'),
        ('Angular',             'both'),
        ('Django',              'both'),
        ('Spring Boot',         'both'),
        ('Flask',               'both'),
        # Right — desired destinations
        ('Next.js',             'want_to_work_with'),
        ('Vue.js',              'want_to_work_with'),
        ('FastAPI',             'want_to_work_with'),
        ('Svelte',              'want_to_work_with'),
        ('ASP.NET Core',        'want_to_work_with'),
    ],

    'Cloud & DevOps': [
        # Left — currently used but not the destination
        ('npm',                 'worked_with'),
        ('Pip',                 'worked_with'),
        ('Homebrew',            'worked_with'),
        ('APT',                 'worked_with'),
        ('Google Cloud',        'worked_with'),
        ('Make',                'worked_with'),
        ('Azure',               'worked_with'),
        ('Webpack',             'worked_with'),
        ('Yarn',                'worked_with'),
        # Both — core infrastructure
        ('AWS',                 'both'),
        ('Docker',              'both'),
        ('Vite',                'both'),
        # Right — strong pull destinations
        ('Kubernetes',          'want_to_work_with'),
        ('Cargo',               'want_to_work_with'),
        ('Terraform',           'want_to_work_with'),
        ('Cloudflare',          'want_to_work_with'),
    ],

    'Dev IDEs': [
        # Left — currently used editors, some legacy
        ('Android Studio',          'worked_with'),
        ('Jupyter Nb/JupyterLab',   'worked_with'),
        ('Notepad++',               'worked_with'),
        ('Visual Studio',           'worked_with'),
        ('Vim',                     'worked_with'),
        # Both — dominant, sticky
        ('Visual Studio Code',      'both'),
        # Right — high pull / AI-native IDEs rising
        ('Claude Code',             'want_to_work_with'),
        ('Cursor',                  'want_to_work_with'),
        ('IntelliJ IDEA',           'want_to_work_with'),
        ('Neovim',                  'want_to_work_with'),
        ('Zed',                     'want_to_work_with'),
    ],

    'Large Language Models': [
        # Left — dominant current platform
        ('OpenAI GPT',          'worked_with'),
        # Both — used and wanted
        ('Gemini Flash',        'both'),
        ('OpenAI Reasoning',    'both'),
        ('OpenAI Image',        'both'),
        ('DeepSeek Reasoning',  'both'),
        ('DeepSeek General',    'both'),
        ('Meta Llama',          'both'),
        ('Perplexity Sonar',    'both'),
        ('Mistral',             'both'),
        # Right — high pull
        ('Gemini Reasoning',    'want_to_work_with'),
        ('Claude Sonnet',       'want_to_work_with'),
        ('X Grok',              'want_to_work_with'),
        ('Alibaba Qwen',        'want_to_work_with'),
    ],

    'Collaboration Tools': [
        # Left — currently used, some legacy PM tools
        ('Asana',               'worked_with'),
        ('Miro',                'worked_with'),
        ('Clickup',             'worked_with'),
        ('Confluence',          'worked_with'),
        ('Trello',              'worked_with'),
        ('Lucid / Lucidchart',  'worked_with'),
        ('Doxygen',             'worked_with'),
        ('Microsoft Planner',   'worked_with'),
        # Both — widely used and retained
        ('Jira',                'both'),
        ('Azure DevOps',        'both'),
        ('Notion',              'both'),
        ('Google Workspace',    'both'),
        ('Wikis',               'both'),
        ('Google Colab',        'both'),
        # Right — desired destinations
        ('Stack Overflow for Teams', 'want_to_work_with'),
        ('GitHub',              'want_to_work_with'),
        ('Markdown File',       'want_to_work_with'),
        ('Obsidian',            'want_to_work_with'),
        ('GitLab',              'want_to_work_with'),
        ('Linear',              'want_to_work_with'),
    ],

    'Community Platforms': [
        # Left — currently used but flowing to newer destinations
        ('Medium',              'worked_with'),
        ('LinkedIn',            'worked_with'),
        ('Reddit',              'worked_with'),
        ('X (Twitter)',         'worked_with'),
        ('Slack (public)',      'worked_with'),
        # Both — core developer communities
        ('Discord',             'both'),
        ('Stack Exchange',      'both'),
        ('YouTube',             'both'),
        # Right — destination platforms
        ('GitHub (public)',     'want_to_work_with'),
        ('Stack Overflow',      'want_to_work_with'),
        ('Hacker News',         'want_to_work_with'),
        ('Bluesky',             'want_to_work_with'),
    ],

    'Trending Topics': [
        # Left — established/early topics already in use
        ('Google Gemini',       'worked_with'),
        ('.NET 8+',             'worked_with'),
        # Both — broad adoption and continued interest
        ('Large language model','both'),
        ('Tailwind CSS 4',      'both'),
        ('Ollama',              'both'),
        # Right — high future pull
        ('RAG',                 'want_to_work_with'),
        ('Shadcn/ui',           'want_to_work_with'),
        ('uv',                  'want_to_work_with'),
        ('LangGraph',           'want_to_work_with'),
        ('C++23',               'want_to_work_with'),
        ('Pydantic',            'want_to_work_with'),
    ],
}


def run():
    with app.app_context():
        count = 0
        for category, items in SANKEY_DATA.items():
            for tech, role in items:
                execute("""
                    INSERT INTO survey_benchmarks
                        (survey_source, survey_year, category, technology,
                         usage_pct, context, source_url, sankey_role)
                    VALUES (%s, %s, %s, %s, 0, 'all_respondents',
                            'https://survey.stackoverflow.co/2025', %s)
                    ON CONFLICT (survey_source, survey_year, category, technology, context)
                    DO UPDATE SET sankey_role = EXCLUDED.sankey_role
                """, (SOURCE, YEAR, category, tech, role))
                count += 1

        print(f'Updated sankey_role for {count} technologies across '
              f'{len(SANKEY_DATA)} categories.')

        # Quick verify
        from app.db import query, to_dict
        summary = [to_dict(r) for r in query("""
            SELECT sankey_role, COUNT(*) AS n
            FROM survey_benchmarks
            WHERE sankey_role IS NOT NULL
            GROUP BY sankey_role ORDER BY n DESC
        """)]
        print('Role breakdown:', summary)


if __name__ == '__main__':
    run()
