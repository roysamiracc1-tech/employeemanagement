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

class TestLoginPageStructure:
    """The login page must be a clean split-panel layout with correct assets."""

    def _html(self, client):
        with patch('app.routes.auth.query', return_value=[]):
            status, html = get_html(client, '/login')
        assert status == 200, f"Login page returned {status}"
        return html

    def test_returns_200(self, client):
        with patch('app.routes.auth.query', return_value=[]):
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
        demo = [{
            'name': 'Oliver Hartmann', 'email': 'oliver@company.com',
            'job_title': 'CTO', 'roles': ['SYSTEM_ADMIN', 'EMPLOYEE'],
        }]
        with patch('app.routes.auth.query', return_value=demo):
            _, html = get_html(client, '/login')
        assert 'demo-chip' in html,   "Demo account chips not rendered"
        assert 'demo-grid' in html,   "Demo account grid not rendered"
        assert 'quickLogin' in html,  "quickLogin JS function missing"
        assert 'Oliver Hartmann' in html

    def test_demo_badges_show_role_labels(self, client):
        demo = [{'name': 'A B', 'email': 'a@b.com', 'job_title': 'Dev',
                 'roles': ['SYSTEM_ADMIN', 'EMPLOYEE']}]
        with patch('app.routes.auth.query', return_value=demo):
            _, html = get_html(client, '/login')
        assert 'Tech Admin' in html, "SYSTEM_ADMIN should display as 'Tech Admin'"

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
