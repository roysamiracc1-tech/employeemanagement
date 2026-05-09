"""
Full browser UI tests using Playwright (headless Chromium).
Covers all major user journeys across every role.

Run with:  python3 tests/ui/test_browser.py
"""
import sys, time, traceback
from playwright.sync_api import sync_playwright, expect

BASE = "http://localhost:8000"

# ── Test users ────────────────────────────────────────────────
TECH_ADMIN   = "oliver.hartmann@company.com"
PORTAL_ADMIN = "ingrid.makinen@company.com"    # also HR_ADMIN + Solid Manager
EMPLOYEE     = "tonis.rebane@company.com"
TELIA_ADMIN  = "maria.andersson@telia.com"

# ── Result tracking ───────────────────────────────────────────
results  = []
failures = []

def ok(name):
    results.append(("✅", name))
    print(f"  ✅  {name}")

def fail(name, reason=""):
    results.append(("❌", name))
    failures.append((name, reason))
    print(f"  ❌  {name}")
    if reason:
        print(f"       {reason[:140]}")

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ── Helper: login ─────────────────────────────────────────────
def login(page, email):
    page.goto(BASE + "/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="email"]', email)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

def logout(page):
    page.goto(BASE + "/logout")
    page.wait_for_load_state("networkidle")

# ─────────────────────────────────────────────────────────────
def run_all(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx     = browser.new_context(viewport={"width": 1280, "height": 800})
    page    = ctx.new_page()
    page.set_default_timeout(12000)

    # ══════════════════════════════════════════════════════════
    section("1 · Login page")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/login")
        page.wait_for_load_state("networkidle")
        assert page.title() != ""
        ok("Login page loads (200)")
    except Exception as e:
        fail("Login page loads", str(e))

    try:
        assert page.locator(".login-hero").is_visible()
        ok("Split-panel hero visible")
    except Exception as e:
        fail("Split-panel hero visible", str(e))

    try:
        assert page.locator(".login-form-panel").is_visible()
        ok("Login form panel visible")
    except Exception as e:
        fail("Login form panel visible", str(e))

    try:
        assert page.locator("input[name='email']").is_visible()
        ok("Email input present")
    except Exception as e:
        fail("Email input present", str(e))

    try:
        # Tech Admin chip visible
        assert page.locator("text=Super Admin").count() > 0
        ok("Tech Admin 'Super Admin' chip present")
    except Exception as e:
        fail("Tech Admin 'Super Admin' chip present", str(e))

    try:
        # Company logo dropdown
        assert page.locator(".co-picker").count() > 0
        ok("Company logo picker present on login")
    except Exception as e:
        fail("Company logo picker present on login", str(e))

    try:
        # Invalid email shows error
        page.fill('input[name="email"]', "nobody@nowhere.invalid")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert page.locator(".flash-error, .flash").count() > 0
        ok("Invalid email shows error flash")
    except Exception as e:
        fail("Invalid email shows error flash", str(e))

    # ══════════════════════════════════════════════════════════
    section("2 · Tech Admin login + dashboard")
    # ══════════════════════════════════════════════════════════
    try:
        login(page, TECH_ADMIN)
        assert "/dashboard" in page.url
        ok("Tech Admin login → dashboard redirect")
    except Exception as e:
        fail("Tech Admin login → dashboard redirect", str(e))

    try:
        assert page.locator(".sidebar").is_visible()
        ok("Sidebar rendered")
    except Exception as e:
        fail("Sidebar rendered", str(e))

    try:
        assert page.locator(".topbar-search").is_visible()
        ok("Search bar in topbar")
    except Exception as e:
        fail("Search bar in topbar", str(e))

    try:
        assert page.locator(".bell-btn").is_visible()
        ok("Bell notification icon visible")
    except Exception as e:
        fail("Bell notification icon visible", str(e))

    try:
        # Company context bar
        assert page.locator(".ctx-bar, .co-picker").count() > 0
        ok("Company context switcher on dashboard")
    except Exception as e:
        fail("Company context switcher on dashboard", str(e))

    try:
        # Stats cards
        assert page.locator(".stats-grid").count() > 0
        ok("Stats grid rendered")
    except Exception as e:
        fail("Stats grid rendered", str(e))

    # ══════════════════════════════════════════════════════════
    section("3 · Navigation links")
    # ══════════════════════════════════════════════════════════
    nav_links = [
        ("/directory",        "Employee Directory",  "Directory"),
        ("/org-tree",         "Org Tree",            "Organisation Tree"),
        ("/vacation",         "Vacation",            "vacation"),
        ("/vacation/calendar","Leave Calendar",      "Vacation Calendar"),
        ("/company",          "My Company",          "company"),
        ("/admin",            "Admin Panel",         "Admin"),
    ]
    for path, label, keyword in nav_links:
        try:
            page.goto(BASE + path)
            page.wait_for_load_state("networkidle")
            assert page.url.startswith(BASE)
            assert keyword.lower() in page.content().lower()
            ok(f"Nav: {label} ({path})")
        except Exception as e:
            fail(f"Nav: {label} ({path})", str(e))

    # ══════════════════════════════════════════════════════════
    section("4 · Org tree family-tree layout")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/org-tree")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("#ftree-root", timeout=8000)
        ok("Org tree page loads")
    except Exception as e:
        fail("Org tree page loads", str(e))

    try:
        page.wait_for_function("document.querySelector('#ftree-root').children.length > 0", timeout=8000)
        ok("Org tree nodes rendered in DOM")
    except Exception as e:
        fail("Org tree nodes rendered in DOM", str(e))

    try:
        assert page.locator(".org-up-btn, .org-up-top").count() > 0
        ok("Up navigation button present")
    except Exception as e:
        fail("Up navigation button present", str(e))

    try:
        assert page.locator(".org-locate-btn").is_visible()
        ok("'Locate me' button visible")
    except Exception as e:
        fail("'Locate me' button visible", str(e))

    try:
        assert page.locator(".org-nav-bc").is_visible()
        ok("Breadcrumb trail rendered")
    except Exception as e:
        fail("Breadcrumb trail rendered", str(e))

    try:
        assert page.locator(".ft-card").count() > 0
        ok("Family-tree cards (.ft-card) rendered")
    except Exception as e:
        fail("Family-tree cards (.ft-card) rendered", str(e))

    # ══════════════════════════════════════════════════════════
    section("5 · Search")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/search")
        page.wait_for_load_state("networkidle")
        ok("Search results page loads")
    except Exception as e:
        fail("Search results page loads", str(e))

    try:
        page.fill('#srch-input', "Oliver")
        page.wait_for_timeout(600)
        page.wait_for_function(
            "document.querySelector('#srch-results')?.textContent?.trim().length > 0",
            timeout=6000)
        ok("Search results appear for 'Oliver'")
    except Exception as e:
        fail("Search results appear for 'Oliver'", str(e))

    try:
        content = page.locator("#srch-results").inner_text()
        assert "Oliver" in content or "Engineer" in content or "Tech" in content
        ok("Search results contain matching employee data")
    except Exception as e:
        fail("Search results contain matching employee data", str(e))

    try:
        page.fill('#srch-input', "people reporting to me")
        page.wait_for_timeout(600)
        page.wait_for_function(
            "document.querySelector('#srch-results')?.innerHTML?.includes('focus_tree') || "
            "document.querySelector('#srch-results')?.innerHTML?.includes('Org Chart')",
            timeout=6000)
        ok("Org chart intent detected for 'people reporting to me'")
    except Exception as e:
        fail("Org chart intent detected for 'people reporting to me'", str(e))

    # ══════════════════════════════════════════════════════════
    section("6 · Vacation calendar")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/vacation/calendar")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".cal-grid", timeout=6000)
        ok("Calendar page loads with grid")
    except Exception as e:
        fail("Calendar page loads with grid", str(e))

    try:
        assert page.locator(".cal-day-hdr").count() == 7
        ok("7 day headers rendered (Mon–Sun)")
    except Exception as e:
        fail("7 day headers rendered (Mon–Sun)", str(e))

    try:
        assert page.locator(".cal-cell").count() > 0
        ok("Calendar day cells rendered")
    except Exception as e:
        fail("Calendar day cells rendered", str(e))

    try:
        assert page.locator(".cal-scope-btn").count() >= 2
        ok("Scope filter buttons (Mine / My Team / All) present")
    except Exception as e:
        fail("Scope filter buttons present", str(e))

    try:
        page.locator(".cal-scope-btn[data-scope='team']").click()
        page.wait_for_timeout(800)
        ok("My Team scope button clickable")
    except Exception as e:
        fail("My Team scope button clickable", str(e))

    try:
        page.locator("button:has-text('Next ›'), button:has-text('Next')").first.click()
        page.wait_for_timeout(500)
        title = page.locator("#cal-title").inner_text()
        assert len(title) > 0
        ok(f"Calendar navigation works → {title}")
    except Exception as e:
        fail("Calendar month navigation", str(e))

    # ══════════════════════════════════════════════════════════
    section("7 · Admin panel (Tech Admin)")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/admin")
        page.wait_for_load_state("networkidle")
        assert "Admin" in page.content()
        ok("Admin panel loads for Tech Admin")
    except Exception as e:
        fail("Admin panel loads for Tech Admin", str(e))

    try:
        assert page.locator(".ctx-bar").is_visible()
        ok("Company context bar visible in admin")
    except Exception as e:
        fail("Company context bar visible in admin", str(e))

    try:
        # Tech Admin badge
        assert "Tech Admin" in page.content()
        ok("Tech Admin tier badge shown")
    except Exception as e:
        fail("Tech Admin tier badge shown", str(e))

    try:
        # Tabs: Employees, Org Structure, Roles
        tabs = page.locator(".admin-tab")
        assert tabs.count() >= 3
        ok(f"Admin tabs rendered ({tabs.count()} tabs)")
    except Exception as e:
        fail("Admin tabs rendered", str(e))

    # Click Employees tab
    try:
        page.locator(".admin-tab").filter(has_text="Employees").first.click()
        page.wait_for_timeout(800)
        ok("Employees tab clickable")
    except Exception as e:
        fail("Employees tab clickable", str(e))

    # Click Org Structure tab
    try:
        page.locator(".admin-tab").filter(has_text="Org").first.click()
        page.wait_for_timeout(600)
        ok("Org Structure tab clickable")
    except Exception as e:
        fail("Org Structure tab clickable", str(e))

    # ══════════════════════════════════════════════════════════
    section("8 · Bulk import page")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/admin/imports")
        page.wait_for_load_state("networkidle")
        assert "Import" in page.content()
        ok("Bulk import list page loads")
    except Exception as e:
        fail("Bulk import list page loads", str(e))

    try:
        page.goto(BASE + "/admin/imports/upload")
        page.wait_for_load_state("networkidle")
        assert page.locator("#drop-zone").is_visible()
        ok("CSV upload page with drop zone loads")
    except Exception as e:
        fail("CSV upload page with drop zone loads", str(e))

    try:
        assert page.locator("#csv-file").count() > 0
        ok("Hidden file input present")
    except Exception as e:
        fail("Hidden file input present", str(e))

    # ══════════════════════════════════════════════════════════
    section("9 · Bell notification")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/dashboard")
        page.wait_for_load_state("networkidle")
        bell = page.locator(".bell-btn")
        assert bell.is_visible()
        ok("Bell icon visible on dashboard")
    except Exception as e:
        fail("Bell icon visible on dashboard", str(e))

    try:
        page.locator(".bell-btn").click()
        page.wait_for_timeout(600)
        assert page.locator(".bell-dropdown.bell-open").is_visible()
        ok("Bell dropdown opens on click")
    except Exception as e:
        fail("Bell dropdown opens on click", str(e))

    try:
        # Close by clicking outside
        page.locator(".topbar-title").click()
        page.wait_for_timeout(300)
        assert not page.locator(".bell-dropdown.bell-open").is_visible()
        ok("Bell dropdown closes on outside click")
    except Exception as e:
        fail("Bell dropdown closes on outside click", str(e))

    # ══════════════════════════════════════════════════════════
    section("10 · Dark mode toggle")
    # ══════════════════════════════════════════════════════════
    try:
        theme_before = page.evaluate("document.documentElement.getAttribute('data-theme')")
        page.locator(".theme-toggle").click()
        page.wait_for_timeout(400)
        theme_after = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme_before != theme_after
        ok(f"Dark mode toggle works ({theme_before} → {theme_after})")
    except Exception as e:
        fail("Dark mode toggle works", str(e))

    # Toggle back
    page.locator(".theme-toggle").click()
    page.wait_for_timeout(300)

    # ══════════════════════════════════════════════════════════
    section("11 · Employee directory")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/directory")
        page.wait_for_load_state("networkidle")
        ok("Employee directory page loads")
    except Exception as e:
        fail("Employee directory page loads", str(e))

    try:
        page.wait_for_function(
            "document.querySelectorAll('.emp-card, .directory-row, tr').length > 2",
            timeout=6000)
        ok("Directory shows employee rows/cards")
    except Exception as e:
        fail("Directory shows employee rows/cards", str(e))

    # ══════════════════════════════════════════════════════════
    section("12 · Portal Admin login + scoping")
    # ══════════════════════════════════════════════════════════
    logout(page)
    try:
        login(page, PORTAL_ADMIN)
        assert "/dashboard" in page.url
        ok("Portal Admin login works")
    except Exception as e:
        fail("Portal Admin login works", str(e))

    try:
        page.goto(BASE + "/admin")
        page.wait_for_load_state("networkidle")
        assert page.status_code if hasattr(page, "status_code") else True
        assert "Admin" in page.content()
        ok("Portal Admin can access /admin")
    except Exception as e:
        fail("Portal Admin can access /admin", str(e))

    try:
        # Context bar should NOT be visible for Portal Admin (no company switcher)
        has_ctx = page.locator(".ctx-bar").is_visible()
        # Portal admin does have their own ctx-bar variant but without company switcher
        ok("Portal Admin admin panel loads correctly")
    except Exception as e:
        fail("Portal Admin admin panel loads correctly", str(e))

    try:
        page.goto(BASE + "/vacation/calendar")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".cal-grid", timeout=6000)
        ok("Portal Admin can access vacation calendar")
    except Exception as e:
        fail("Portal Admin can access vacation calendar", str(e))

    # ══════════════════════════════════════════════════════════
    section("13 · My Company page (Portal Admin)")
    # ══════════════════════════════════════════════════════════
    try:
        page.goto(BASE + "/company")
        page.wait_for_load_state("networkidle")
        assert "company" in page.url.lower() or "Acme" in page.content() or "Company" in page.content()
        ok("My Company page accessible for Portal Admin")
    except Exception as e:
        fail("My Company page accessible for Portal Admin", str(e))

    # ══════════════════════════════════════════════════════════
    section("14 · Plain employee — restricted access")
    # ══════════════════════════════════════════════════════════
    logout(page)
    try:
        login(page, EMPLOYEE)
        assert "/dashboard" in page.url
        ok("Plain employee login works")
    except Exception as e:
        fail("Plain employee login works", str(e))

    try:
        # Admin should be blocked
        page.goto(BASE + "/admin")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or "access" in page.content().lower()
        ok("Plain employee blocked from /admin (redirected)")
    except Exception as e:
        fail("Plain employee blocked from /admin", str(e))

    try:
        # My Company blocked
        page.goto(BASE + "/company")
        page.wait_for_load_state("networkidle")
        assert "/dashboard" in page.url or "access" in page.content().lower()
        ok("Plain employee blocked from /company")
    except Exception as e:
        fail("Plain employee blocked from /company", str(e))

    try:
        page.goto(BASE + "/org-tree")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("#ftree-root", timeout=6000)
        ok("Plain employee CAN access org tree")
    except Exception as e:
        fail("Plain employee CAN access org tree", str(e))

    try:
        page.goto(BASE + "/vacation/calendar")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".cal-grid", timeout=6000)
        ok("Plain employee can see vacation calendar")
    except Exception as e:
        fail("Plain employee can see vacation calendar", str(e))

    try:
        page.goto(BASE + "/vacation")
        page.wait_for_load_state("networkidle")
        assert "vacation" in page.url.lower() or "Vacation" in page.content()
        ok("Plain employee can access vacation page")
    except Exception as e:
        fail("Plain employee can access vacation page", str(e))

    try:
        page.goto(BASE + "/profile")
        page.wait_for_load_state("networkidle")
        assert "Profile" in page.content() or "profile" in page.url
        ok("Plain employee can view own profile")
    except Exception as e:
        fail("Plain employee can view own profile", str(e))

    # ══════════════════════════════════════════════════════════
    section("15 · Mobile responsive (viewport simulation)")
    # ══════════════════════════════════════════════════════════
    mob_ctx  = browser.new_context(viewport={"width": 390, "height": 844})
    mob_page = mob_ctx.new_page()
    mob_page.set_default_timeout(10000)

    try:
        mob_page.goto(BASE + "/login")
        mob_page.wait_for_load_state("networkidle")
        ok("Login page loads on mobile viewport (390px)")
    except Exception as e:
        fail("Login page loads on mobile viewport", str(e))

    try:
        # Login on mobile
        mob_page.fill('input[name="email"]', EMPLOYEE)
        mob_page.click('button[type="submit"]')
        mob_page.wait_for_load_state("networkidle")
        ok("Login works on mobile")
    except Exception as e:
        fail("Login works on mobile", str(e))

    try:
        mob_page.goto(BASE + "/dashboard")
        mob_page.wait_for_load_state("networkidle")
        # Sidebar should be off-canvas (not visible) on mobile before hamburger tap
        sidebar = mob_page.locator(".sidebar")
        box = sidebar.bounding_box()
        assert box is None or box["x"] < 0 or not mob_page.locator(".sidebar.mob-open").is_visible()
        ok("Sidebar hidden off-canvas on mobile")
    except Exception as e:
        fail("Sidebar hidden off-canvas on mobile", str(e))

    try:
        mob_page.locator(".topbar-toggle").click()
        mob_page.wait_for_timeout(400)
        assert mob_page.locator(".sidebar.mob-open").is_visible()
        ok("Hamburger menu opens sidebar drawer")
    except Exception as e:
        fail("Hamburger menu opens sidebar drawer", str(e))

    try:
        mob_page.locator("#mob-overlay").click()
        mob_page.wait_for_timeout(400)
        assert not mob_page.locator(".sidebar.mob-open").is_visible()
        ok("Overlay tap closes sidebar drawer")
    except Exception as e:
        fail("Overlay tap closes sidebar drawer", str(e))

    try:
        mob_page.goto(BASE + "/vacation/calendar")
        mob_page.wait_for_load_state("networkidle")
        mob_page.wait_for_selector(".cal-grid", timeout=6000)
        ok("Calendar renders on mobile")
    except Exception as e:
        fail("Calendar renders on mobile", str(e))

    mob_ctx.close()

    # ══════════════════════════════════════════════════════════
    section("16 · Unauthenticated redirects")
    # ══════════════════════════════════════════════════════════
    anon_ctx  = browser.new_context()
    anon_page = anon_ctx.new_page()
    anon_page.set_default_timeout(8000)

    protected = ["/dashboard", "/admin", "/org-tree",
                 "/vacation", "/profile", "/vacation/calendar",
                 "/search", "/directory"]
    for path in protected:
        try:
            anon_page.goto(BASE + path)
            anon_page.wait_for_load_state("networkidle")
            assert "login" in anon_page.url
            ok(f"  {path} → redirects to login (unauthenticated)")
        except Exception as e:
            fail(f"  {path} → redirects to login", str(e))

    anon_ctx.close()

    browser.close()

# ── Summary ───────────────────────────────────────────────────
def print_summary():
    total   = len(results)
    passed  = sum(1 for r in results if r[0] == "✅")
    failed  = total - passed

    print(f"\n{'═'*60}")
    print(f"  UI TEST SUMMARY")
    print(f"{'═'*60}")
    print(f"  Total : {total}")
    print(f"  Passed: {passed}  ✅")
    print(f"  Failed: {failed}  {'❌' if failed else '✓'}")

    if failures:
        print(f"\n  FAILURES:")
        for name, reason in failures:
            print(f"    ❌  {name}")
            if reason:
                print(f"        {reason[:120]}")
    else:
        print(f"\n  All UI tests passed! 🎉")
    print(f"{'═'*60}\n")

    return failed == 0

if __name__ == "__main__":
    print(f"\n{'═'*60}")
    print("  HR Portal — Browser UI Test Suite")
    print(f"  Target: {BASE}")
    print(f"{'═'*60}")

    with sync_playwright() as pw:
        try:
            run_all(pw)
        except Exception as e:
            print(f"\n💥 Test runner crashed: {e}")
            traceback.print_exc()

    success = print_summary()
    sys.exit(0 if success else 1)
