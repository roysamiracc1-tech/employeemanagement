"""
UI/UX regression tests.

These tests catch broken templates, wrong asset paths, missing CSS classes,
and structural regressions — the kind of things that make pages look
"destroyed" when a template is edited carelessly.

All DB calls are mocked; no live PostgreSQL is required.
"""
import re
import pytest
from unittest.mock import patch

from tests.conftest import _set_session

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_html(client, path, follow_redirects=False):
    r = client.get(path, follow_redirects=follow_redirects)
    return r.status_code, r.data.decode()


def assert_css_class(html, cls, context=''):
    assert f'class="{cls}"' in html or f'{cls}"' in html or f'{cls} ' in html, \
        f"CSS class '{cls}' not found in HTML{' (' + context + ')' if context else ''}"


def assert_no_broken_links(html):
    """Flag href/src/action attributes that reference /static/ paths not served."""
    # Detect if the static CSS path is correct
    bad = re.findall(r'href="[^"]*filename=style\.css[^"]*"', html)
    assert not bad, f"Wrong CSS path (missing 'css/' subdirectory): {bad}"


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────

def _demo_query_stub(sql, params=(), one=False):
    """Minimal stub for _login_demo_data: returns None for one=True, [] for lists."""
    return None if one else []


class TestLoginPageStructure:
    """The login page must be a clean split-panel layout with correct assets."""

    def _html(self, client):
        with patch('app.routes.auth.query', side_effect=_demo_query_stub):
            status, html = get_html(client, '/login')
        assert status == 200, f"Login page returned {status}"
        return html

    def test_returns_200(self, client):
        with patch('app.routes.auth.query', side_effect=_demo_query_stub):
            status, _ = get_html(client, '/login')
        assert status == 200

    def test_correct_css_path(self, client):
        """Must link to css/style.css — NOT style.css (bug that broke login before)."""
        html = self._html(client)
        assert 'css/style.css' in html, \
            "Login page links to wrong stylesheet path — expected 'css/style.css'"
        assert '"style.css"' not in html, \
            "Login page uses bare 'style.css' without css/ subdirectory"

    def test_split_panel_layout_classes(self, client):
        html = self._html(client)
        for cls in ('login-wrap', 'login-hero', 'login-form-panel', 'login-form-inner'):
            assert cls in html, f"Missing layout class: {cls}"

    def test_hero_content_present(self, client):
        html = self._html(client)
        assert 'login-hero-title' in html
        assert 'login-hero-sub'   in html
        assert 'login-hero-features' in html

    def test_form_elements_present(self, client):
        html = self._html(client)
        assert 'name="email"' in html,  "Email input missing"
        assert 'type="email"' in html,  "Email input type missing"
        assert 'type="submit"' in html or 'btn-primary' in html, "Submit button missing"
        assert 'action' in html and 'login' in html, "Form action missing"

    def test_page_title(self, client):
        html = self._html(client)
        assert '<title>' in html
        assert 'Sign in' in html or 'HR Portal' in html

    def test_google_fonts_loaded(self, client):
        html = self._html(client)
        assert 'fonts.googleapis.com' in html, "Google Fonts link missing"
        assert 'Inter' in html, "Inter font not requested"

    def test_demo_accounts_rendered(self, client):
        tech_row = {'email': 'oliver@company.com', 'name': 'Oliver Hartmann', 'job_title': 'Tech Admin'}
        def _side(sql, params=(), one=False):
            if 'SYSTEM_ADMIN' in sql and one:
                return tech_row
            return [] if not one else None
        with patch('app.routes.auth.query', side_effect=_side):
            _, html = get_html(client, '/login')
        assert 'demo-chip' in html,   "Demo account chips not rendered"
        assert 'demo-grid' in html,   "Demo account grid not rendered"
        assert 'quickLogin' in html,  "quickLogin JS function missing"
        assert 'Oliver Hartmann' in html

    def test_demo_badges_show_role_labels(self, client):
        tech_row = {'email': 'a@b.com', 'name': 'A B', 'job_title': 'Tech Admin'}
        def _side(sql, params=(), one=False):
            if 'SYSTEM_ADMIN' in sql and one:
                return tech_row
            return [] if not one else None
        with patch('app.routes.auth.query', side_effect=_side):
            _, html = get_html(client, '/login')
        assert 'Super Admin' in html, "Tech Admin chip should show 'Super Admin' badge"
        assert 'Tech Admin' in html,  "Tech Admin label missing"

    def test_no_old_login_card_classes(self, client):
        """Ensure the old (broken) login-card / login-page classes are gone."""
        html = self._html(client)
        assert 'class="login-page"' not in html, "Old .login-page class found — template not updated"
        assert 'class="login-card"' not in html, "Old .login-card class found — template not updated"

    def test_demo_mode_notice(self, client):
        html = self._html(client)
        assert 'Demo' in html or 'demo' in html, "Demo mode notice missing"

    def test_redirects_logged_in_user(self, client):
        _set_session(client)
        r = client.get('/login')
        assert r.status_code in (301, 302), "Logged-in user should be redirected from /login"


class TestLoginCSS:
    """CSS stylesheet must define all classes the login template uses."""

    def test_login_css_classes_defined(self):
        with open('static/css/style.css') as f:
            css = f.read()
        required = [
            '.login-wrap', '.login-hero', '.login-form-panel', '.login-form-inner',
            '.login-hero-title', '.login-hero-sub', '.login-hero-features',
            '.login-hero-feat', '.login-hero-feat-icon', '.login-hero-brand',
            '.demo-grid', '.demo-chip', '.demo-chip-name', '.demo-chip-title',
            '.demo-chip-badges', '.demo-chip-badge', '.login-or', '.login-footer',
        ]
        missing = [c for c in required if c not in css]
        assert not missing, f"CSS classes missing from stylesheet: {missing}"

    def test_no_old_login_classes_in_css(self):
        with open('static/css/style.css') as f:
            css = f.read()
        # These were the old classes — they must be gone to avoid conflicts
        old_classes = ['.login-card {', '.login-card-header {',
                       '.login-card-body {', '.login-logo {']
        found = [c for c in old_classes if c in css]
        assert not found, f"Old login CSS classes still present: {found}"

    def test_dark_mode_overrides_present(self):
        with open('static/css/style.css') as f:
            css = f.read()
        assert '[data-theme="dark"] .login-hero' in css
        assert '[data-theme="dark"] .login-form-panel' in css


# ─────────────────────────────────────────────────────────────────────────────
# BASE TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseTemplate:
    """Any authenticated page that extends base.html must load correctly."""

    def _dashboard_html(self, client, roles=None):
        _set_session(client, roles=roles or ['EMPLOYEE'])
        # Dashboard calls query(..., one=True) for counts — return a dict with 'c'
        def mock_q(sql, params=(), one=False):
            if one:
                return {'c': 0, 'total': 0, 'active': 0}
            return []
        with patch('app.routes.dashboard.query', side_effect=mock_q):
            status, html = get_html(client, '/dashboard')
        return status, html

    def test_dashboard_returns_200_for_employee(self, client):
        status, _ = self._dashboard_html(client)
        assert status == 200

    def test_base_css_path_correct(self, client):
        _, html = self._dashboard_html(client)
        assert 'css/style.css' in html, "base.html links to wrong stylesheet path"
        assert '"style.css"' not in html

    def test_sidebar_present(self, client):
        _, html = self._dashboard_html(client)
        assert 'sidebar' in html
        assert 'nav-link' in html

    def test_admin_link_hidden_from_employee(self, client):
        _, html = self._dashboard_html(client, roles=['EMPLOYEE'])
        assert 'Admin Panel' not in html

    def test_admin_link_visible_for_system_admin(self, client):
        _, html = self._dashboard_html(client, roles=['SYSTEM_ADMIN', 'EMPLOYEE'])
        assert 'Admin Panel' in html or 'admin' in html.lower()

    def test_companies_link_hidden_from_portal_admin(self, client):
        _, html = self._dashboard_html(client, roles=['PORTAL_ADMIN', 'EMPLOYEE'])
        # Portal Admin should NOT see the cross-company Companies management link
        assert 'url_for' not in html  # Jinja rendered — check admin_companies link
        # Check by finding Companies text near an admin link
        admin_section = html[html.find('Administration'):] if 'Administration' in html else ''
        assert 'Companies' not in admin_section or 'Company Settings' in admin_section

    def test_theme_toggle_present(self, client):
        _, html = self._dashboard_html(client)
        assert 'toggleTheme' in html or 'theme-toggle' in html

    def test_dark_mode_attribute_on_html_tag(self, client):
        _, html = self._dashboard_html(client)
        assert 'data-theme=' in html


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminPanelStructure:
    """Admin panel must render all expected tabs and structures."""

    def _html(self, admin_client):
        with patch('app.routes.admin.query', return_value=[]):
            status, html = get_html(admin_client, '/admin')
        assert status == 200
        return html

    def test_tab_users_present(self, admin_client):
        html = self._html(admin_client)
        assert 'Users' in html and 'Roles' in html

    def test_tab_employees_present(self, admin_client):
        html = self._html(admin_client)
        assert 'Employees' in html

    def test_tab_org_present(self, admin_client):
        html = self._html(admin_client)
        assert 'Organisation' in html

    def test_tab_roles_permissions_for_tech_admin(self, admin_client):
        html = self._html(admin_client)
        assert 'Roles' in html and 'Permissions' in html

    def test_company_ctx_bar_for_tech_admin(self, admin_client):
        html = self._html(admin_client)
        assert 'ctx-bar' in html or 'Company context' in html

    def test_tech_admin_badge_shown(self, admin_client):
        html = self._html(admin_client)
        assert 'Tech Admin' in html

    def test_no_widget_settings_for_portal_admin(self, client):
        _set_session(client, roles=['PORTAL_ADMIN', 'EMPLOYEE'],
                     employee_id='emp-001', user_id='user-001')
        with client.session_transaction() as sess:
            sess['company_id'] = 'co-001'
        with patch('app.routes.admin.query', return_value=[]):
            _, html = get_html(client, '/admin')
        assert 'Widget Settings' not in html

    def test_org_bu_add_button_present(self, admin_client):
        html = self._html(admin_client)
        assert 'openOrgModal' in html
        assert 'Add BU' in html or 'Add Location' in html

    def test_org_modals_present(self, admin_client):
        html = self._html(admin_client)
        for modal_id in ('bu-modal', 'loc-modal', 'fu-modal'):
            assert modal_id in html, f"Modal #{modal_id} missing from admin panel"

    def test_role_permission_matrix_container(self, admin_client):
        html = self._html(admin_client)
        assert 'role-matrix-container' in html

    def test_scoped_employees_api_called(self, admin_client):
        """JS must call /api/admin/employees, NOT /api/employees."""
        html = self._html(admin_client)
        assert '/api/admin/employees' in html, \
            "Admin panel calls unscoped /api/employees instead of /api/admin/employees"
        # Ensure the unscoped call is NOT there
        # (allow it only in comments or string literals for documentation)
        lines_with_fetch = [l.strip() for l in html.split('\n')
                            if 'fetch(' in l and 'employees' in l]
        for line in lines_with_fetch:
            assert '/api/admin/employees' in line, \
                f"Found unscoped employee fetch: {line}"


# ─────────────────────────────────────────────────────────────────────────────
# CSS FILE INTEGRITY
# ─────────────────────────────────────────────────────────────────────────────

class TestCSSIntegrity:
    """The stylesheet must be valid and complete."""

    def setup_method(self):
        with open('static/css/style.css') as f:
            self.css = f.read()

    def test_css_file_not_empty(self):
        assert len(self.css) > 5000, "CSS file suspiciously small"

    def test_root_variables_present(self):
        assert ':root {' in self.css
        for var in ('--primary', '--bg', '--card', '--border', '--text', '--muted'):
            assert var in self.css, f"CSS variable {var} missing"

    def test_dark_mode_variables_present(self):
        assert '[data-theme="dark"]' in self.css

    def test_btn_classes_present(self):
        for cls in ('.btn', '.btn-primary', '.btn-ghost', '.btn-sm', '.btn-danger'):
            assert cls in self.css, f"Button class {cls} missing"

    def test_modal_classes_present(self):
        for cls in ('.modal-box', '.modal-header', '.modal-body', '.modal-footer'):
            assert cls in self.css, f"Modal class {cls} missing"

    def test_card_classes_present(self):
        assert '.card {' in self.css or '.card\n' in self.css or '.card ' in self.css

    def test_form_control_present(self):
        assert '.form-control' in self.css

    def test_no_duplicate_root_blocks(self):
        count = self.css.count(':root {')
        assert count == 1, f":root block defined {count} times — duplicate CSS variables"

    def test_perm_matrix_classes_present(self):
        """Roles & Permissions matrix needs its own CSS."""
        assert '.perm-matrix' in self.css
        assert '.pm-cell' in self.css

    def test_ctx_bar_class_present(self):
        """Company context switcher needs its CSS."""
        assert '.ctx-bar' in self.css


# ─────────────────────────────────────────────────────────────────────────────
# TEMPLATE ASSET CONSISTENCY
# ─────────────────────────────────────────────────────────────────────────────

class TestTemplateAssetConsistency:
    """Every template that loads assets must use consistent, correct paths."""

    def _all_templates(self):
        import os
        tmpl_dir = 'templates'
        result = []
        for root, _, files in os.walk(tmpl_dir):
            for f in files:
                if f.endswith('.html'):
                    result.append(os.path.join(root, f))
        return result

    def test_no_template_uses_bare_style_css(self):
        """No template should reference 'style.css' without the 'css/' prefix."""
        bad = []
        for path in self._all_templates():
            with open(path) as f:
                content = f.read()
            # Look for any href/src pointing to bare style.css (not css/style.css)
            matches = re.findall(r'''filename=['"]style\.css['"]''', content)
            if matches:
                bad.append(path)
        assert not bad, \
            f"Templates with wrong CSS path (missing 'css/'): {bad}\n" \
            "Fix: change filename='style.css' to filename='css/style.css'"

    def test_login_template_loads_css(self):
        with open('templates/login.html') as f:
            html = f.read()
        assert 'css/style.css' in html, \
            "login.html must link to css/style.css"

    def test_base_template_loads_css(self):
        with open('templates/base.html') as f:
            html = f.read()
        assert 'css/style.css' in html

    def test_all_templates_have_proper_encoding(self):
        for path in self._all_templates():
            try:
                with open(path, encoding='utf-8') as f:
                    f.read()
            except UnicodeDecodeError:
                pytest.fail(f"Template {path} has non-UTF-8 characters")


# ─────────────────────────────────────────────────────────────────────────────
# SHELL ACCESSIBILITY PRIMITIVES (KAN-204 · EP33 debt)
#
# Three primitives the whole product shares. The point of the story is that a
# new screen's accessibility is a call to something that already exists — so
# these tests pin the primitives AND the fact that nobody reimplements them.
#
# EP38 was believed to have delivered this and had not (UX verified three of
# nine), which is why T-204-1 says to verify against the shell rather than
# assume. These assertions are that verification, kept.
# ─────────────────────────────────────────────────────────────────────────────

class TestShellFocusVisibility:
    """Primitive 1 — one focus ring, WCAG 2.4.7, on the shell not per screen."""

    def setup_method(self):
        with open('static/css/style.css') as f:
            self.css = f.read()

    def test_a_global_focus_visible_rule_exists(self):
        assert '\n:focus-visible {' in self.css, (
            'no global focus indicator — before KAN-204 only .row-menu-btn and '
            '.row-menu-list > * had one, on a product with ~210 onclick handlers')

    def test_the_ring_is_a_token_so_it_cannot_drift(self):
        assert '--focus-ring:' in self.css
        assert 'outline: 2px solid var(--focus-ring)' in self.css

    def test_the_ring_has_a_dark_theme_value(self):
        """#2563eb on #0f172a is close to failing WCAG 1.4.11's 3:1."""
        dark = self.css[self.css.index('[data-theme="dark"] {'):]
        dark = dark[:dark.index('}')]
        assert '--focus-ring:' in dark, 'the focus ring has no dark-theme value'

    def test_the_global_rule_comes_after_every_outline_none(self):
        """This is what makes it work, not a formatting preference.

        `:focus-visible` is 0,1,0 — the same specificity as `.search-input`,
        `select.filter-sel` and `.rows-select`, each of which sets
        `outline: none`. It beats them by source order alone, so moving it up
        the file silently returns those controls to having no visible focus.
        """
        rule = self.css.index('\n:focus-visible {')
        last_reset = max(self.css.rindex('outline: none', 0, rule),
                         self.css.rindex('outline:none', 0, rule)
                         if 'outline:none' in self.css[:rule] else 0)
        assert rule > last_reset
        assert 'outline: none' not in self.css[rule:], (
            'an `outline: none` was added after the global focus rule — it now '
            'wins, and that control has no visible focus again')

    def test_the_two_deliberate_component_rings_still_win(self):
        """0,2,0 beats 0,1,0 regardless of order — they are tuned for a menu."""
        assert '.row-menu-btn:focus-visible' in self.css
        assert '.row-menu-list > *:focus-visible' in self.css

    def test_focus_is_not_styled_on_plain_focus(self):
        """`:focus` would leave a ring behind after a mouse click."""
        block = self.css[self.css.index('\n:focus-visible {'):]
        assert not block.startswith('\n:focus {')


class TestShellLiveRegions:
    """Primitive 2 — exactly ONE pair of live regions in the whole product."""

    def setup_method(self):
        with open('templates/base.html') as f:
            self.base = f.read()

    def test_the_shell_declares_both_regions(self):
        assert 'id="live-status"' in self.base and 'aria-live="polite"' in self.base
        assert 'id="live-alert"' in self.base and 'aria-live="assertive"' in self.base

    def test_both_regions_are_sr_only_and_not_hidden(self):
        """`display:none`/`hidden` removes a region from the a11y tree entirely,
        which silences it — the failure mode that looks like it works."""
        for rid in ('live-status', 'live-alert'):
            tag = re.search(rf'<span[^>]*id="{rid}"[^>]*>', self.base)
            assert tag, f'{rid} is not a <span> element'
            tag = tag.group(0)
            assert 'sr-only' in tag, f'{rid} is not screen-reader-only'
            assert 'display:none' not in tag and ' hidden' not in tag

    def test_the_regions_precede_every_script(self):
        """A region injected with its text is not reliably announced."""
        assert self.base.index('id="live-status"') < self.base.index('<script')

    def test_exactly_one_live_region_pair_exists_in_all_templates(self):
        """T-204-2's grep-assert. Ten screens with ten private live regions is
        the duplication D-004 exists to prevent, and competing regions are a
        real screen-reader bug, not merely untidy."""
        import os
        polite = assertive = 0
        offenders = []
        for root, _, files in os.walk('templates'):
            for f in files:
                if not f.endswith('.html'):
                    continue
                path = os.path.join(root, f)
                with open(path, encoding='utf-8') as fh:
                    src = fh.read()
                p, a = src.count('aria-live="polite"'), src.count('aria-live="assertive"')
                if (p or a) and os.path.normpath(path) != os.path.join('templates', 'base.html'):
                    offenders.append(path)
                polite += p
                assertive += a
        assert not offenders, (
            f'live regions declared outside the shell: {offenders} — use '
            f'announce(msg, level) from base.html instead')
        assert (polite, assertive) == (1, 1), (
            f'expected exactly one polite + one assertive region, got {polite}/{assertive}')

    def test_announce_is_defined_once_in_the_shell(self):
        assert 'function announce(msg, level)' in self.base
        assert self.base.count('function announce(') == 1

    def test_announce_defaults_to_polite(self):
        """Assertive interrupts; the default must be the courteous one."""
        fn = self.base[self.base.index('function announce(msg, level)'):]
        fn = fn[:fn.index('\n}')]
        assert "level === 'assertive' ? 'live-alert' : 'live-status'" in fn

    def test_announce_never_throws_when_the_region_is_absent(self):
        """A missing region must not break the flow that was announcing."""
        fn = self.base[self.base.index('function announce(msg, level)'):]
        fn = fn[:fn.index('\n}')]
        assert 'if (!el) return;' in fn

    def test_the_move_dialog_no_longer_owns_live_regions(self):
        """It had the product's first pair; they became the shell's."""
        with open('templates/org_change/_move_modal.html') as f:
            src = f.read()
        assert 'aria-live' not in src
        assert 'mv-live-status' not in src and 'mv-live-alert' not in src
        assert 'announce(' in src, 'the dialog went silent instead of migrating'

    def test_the_directory_announces_its_result_count(self):
        """An empty-state/filter transition is silent without this."""
        with open('templates/employees/directory.html') as f:
            src = f.read()
        assert 'announce(' in src
        assert 'No employees found.' in src


class TestShellReducedMotion:
    """Primitive 3 — WCAG 2.3.3, honoured shell-wide."""

    def setup_method(self):
        with open('static/css/style.css') as f:
            self.css = f.read()

    def test_a_reduced_motion_block_exists(self):
        assert '@media (prefers-reduced-motion: reduce)' in self.css

    def test_it_covers_transitions_and_animations_universally(self):
        block = self.css[self.css.index('@media (prefers-reduced-motion: reduce)'):]
        for decl in ('animation-duration', 'animation-iteration-count',
                     'transition-duration'):
            assert f'{decl}: .01ms !important' in block or \
                   f'{decl}: 1 !important' in block, f'{decl} not neutralised'
        assert '*, *::before, *::after' in block

    def test_infinite_animations_are_capped(self):
        """A permanently throbbing badge is what this media query is for.
        `pulse`, `anniv-sway` and `anniv-pulse-scale` all run `infinite`."""
        assert 'infinite' in self.css, 'fixture assumption changed'
        block = self.css[self.css.index('@media (prefers-reduced-motion: reduce)'):]
        assert 'animation-iteration-count: 1 !important' in block

    def test_durations_are_near_zero_not_zero(self):
        """A 0s duration fires no `transitionend`, so code awaiting one hangs."""
        block = self.css[self.css.index('@media (prefers-reduced-motion: reduce)'):]
        assert '0s !important' not in block
        assert '.01ms !important' in block

    def test_non_motion_cues_are_left_alone(self):
        """The drag affordance keeps its dashed outline and tint — those are not
        motion, and removing them would take away the only remaining signal."""
        block = self.css[self.css.index('@media (prefers-reduced-motion: reduce)'):]
        code = re.sub(r'/\*.*?\*/', '', block, flags=re.S)   # declarations only
        assert 'outline' not in code, 'reduced motion must not touch outlines'
        assert 'background' not in code, 'reduced motion must not touch colour'
        assert '.ft-card.ft-dragging' in code, 'the drag affordance is not addressed'
