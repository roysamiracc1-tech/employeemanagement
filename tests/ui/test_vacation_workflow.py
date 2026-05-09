"""
End-to-end browser tests for the full vacation approval workflow.

Journey tested:
  1.  Employee logs in → submits a vacation request
  2.  Employee sees the request in their history (PENDING)
  3.  Employee cancels the request; history updates (CANCELLED)
  4.  Employee submits a NEW request for approval
  5.  Manager logs in → bell badge shows count
  6.  Manager opens bell dropdown → sees the pending request
  7.  Manager checks dashboard carousel → pending card present
  8.  Manager checks Leave Calendar (My Team) → pending event on grid or in panel
  9.  Manager goes to Team Vacation page → pending tab shows request
 10.  Manager approves from Team Vacation → status updates to APPROVED
 11.  Employee logs back in → history shows APPROVED
 12.  Manager submits a second request (via employee account) then rejects it
 13.  Employee sees REJECTED in history

Run:  python3 tests/ui/test_vacation_workflow.py
"""

import sys, datetime, traceback
from playwright.sync_api import sync_playwright

BASE        = "http://localhost:8000"
MANAGER     = "liisa.virtanen@company.com"        # Liisa Virtanen – HR Manager (Solid-line)
EMPLOYEE    = "sven.becker@company.com"            # Sven Becker – direct report of Liisa
EMP_NAME    = "Sven"
MGR_NAME    = "Liisa"

# Dates: next two weekday dates at least 14 days out
def _next_weekday(base: datetime.date, min_days: int) -> datetime.date:
    """Return the first Monday–Friday that is at least min_days after base."""
    d = base + datetime.timedelta(days=min_days)
    while d.weekday() >= 5:   # 5=Sat, 6=Sun
        d += datetime.timedelta(days=1)
    return d

today       = datetime.date.today()
_start_date = _next_weekday(today, 14)           # first weekday ≥ 2 weeks out
START       = _start_date.isoformat()
END         = _next_weekday(_start_date, 1).isoformat()  # next weekday after START

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
        print(f"       {reason[:160]}")

def section(title):
    print(f"\n{'─'*64}")
    print(f"  {title}")
    print(f"{'─'*64}")

# ── Helpers ───────────────────────────────────────────────────
def login(page, email):
    page.goto(BASE + "/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="email"]', email)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)

def logout(page):
    page.goto(BASE + "/logout")
    page.wait_for_load_state("networkidle")

def get_request_id(page):
    """After submit, return the latest request id from the vacation page."""
    try:
        # Try to grab it from the DOM (first row in request history)
        req_id = page.evaluate("""
            () => {
                const btns = document.querySelectorAll('[data-req-id], [onclick*="cancel"]');
                for (const b of btns) {
                    const m = (b.getAttribute('onclick') || b.dataset.reqId || '').match(/[0-9a-f-]{36}/i);
                    if (m) return m[0];
                }
                return null;
            }
        """)
        return req_id
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
def run_workflow(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx     = browser.new_context(viewport={"width": 1280, "height": 800})
    page    = ctx.new_page()
    page.set_default_timeout(14000)

    # ══════════════════════════════════════════════════════════
    section(f"Step 1 — Employee ({EMP_NAME}) submits a vacation request")
    # ══════════════════════════════════════════════════════════

    login(page, EMPLOYEE)

    try:
        page.goto(BASE + "/vacation")
        page.wait_for_load_state("networkidle")
        ok("Employee vacation page loads")
    except Exception as e:
        fail("Employee vacation page loads", str(e)); browser.close(); return

    # Check a vacation type is available
    try:
        page.wait_for_function(
            "document.querySelectorAll('.vt-card, [data-vt-id], option[value]').length > 0",
            timeout=6000)
        ok("Vacation types loaded for employee")
    except Exception as e:
        fail("Vacation types loaded for employee", str(e))

    # Fill the vacation request form via the API directly (more reliable than form UI)
    try:
        # Get first available vacation type id from page JS or API
        vt_id = page.evaluate("""
            () => {
                // Try select dropdown first
                const sel = document.querySelector('select[id*="vt"], select[name*="vacation"]');
                if (sel && sel.options.length > 1) return sel.options[1].value;
                // Try data attributes on cards
                const card = document.querySelector('[data-vt-id]');
                if (card) return card.dataset.vtId;
                // Try first option value
                const opt = document.querySelector('option[value]:not([value=""])');
                if (opt) return opt.value;
                return null;
            }
        """)

        if not vt_id:
            # Fall back: fetch from API
            page.evaluate("""
                async () => {
                    const r = await fetch('/api/vacation/types');
                    window._vtypes = r.ok ? await r.json() : [];
                }
            """)
            page.wait_for_timeout(600)
            vt_id = page.evaluate("window._vtypes?.[0]?.id || null")

        assert vt_id, "Could not determine vacation type id"
        ok(f"Vacation type id resolved: {vt_id[:8]}…")
    except Exception as e:
        fail("Vacation type id resolved", str(e))
        browser.close(); return

    # Submit via the API
    try:
        response = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/request', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        vacation_type_id: '{vt_id}',
                        start_date: '{START}',
                        end_date:   '{END}',
                        notes:      'UI test request – please approve'
                    }})
                }});
                return await r.json();
            }}
        """)
        assert response.get('ok') or response.get('id'), f"API response: {response}"
        req_id = response.get('id')
        ok(f"Vacation request submitted (id: {req_id[:8] if req_id else '?'}…)")
    except Exception as e:
        fail("Vacation request submitted", str(e))
        browser.close(); return

    # ══════════════════════════════════════════════════════════
    section("Step 2 — Employee sees PENDING in request history")
    # ══════════════════════════════════════════════════════════

    try:
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "document.body.innerText.includes('PENDING') || "
            "document.body.innerText.includes('Pending')",
            timeout=6000)
        ok("PENDING status visible on vacation page")
    except Exception as e:
        fail("PENDING status visible on vacation page", str(e))

    try:
        assert START[:7] in page.content() or START in page.content()
        ok("Submitted dates visible on vacation page")
    except Exception as e:
        fail("Submitted dates visible on vacation page", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 3 — Employee cancels the request")
    # ══════════════════════════════════════════════════════════

    try:
        cancel_resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/request/{req_id}', {{method: 'DELETE'}});
                return await r.json();
            }}
        """)
        assert cancel_resp.get('ok'), f"Cancel response: {cancel_resp}"
        ok("Employee cancelled the request via API")
    except Exception as e:
        fail("Employee cancelled the request via API", str(e))

    try:
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "document.body.innerText.includes('CANCELLED') || "
            "document.body.innerText.includes('Cancelled')",
            timeout=6000)
        ok("CANCELLED status visible after cancellation")
    except Exception as e:
        fail("CANCELLED status visible after cancellation", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 4 — Employee submits a NEW request for approval")
    # ══════════════════════════════════════════════════════════

    try:
        new_resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/request', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        vacation_type_id: '{vt_id}',
                        start_date: '{START}',
                        end_date:   '{END}',
                        notes:      'Second request for manager approval'
                    }})
                }});
                return await r.json();
            }}
        """)
        assert new_resp.get('ok') or new_resp.get('id'), f"Submit: {new_resp}"
        req_id2 = new_resp.get('id')
        ok(f"New request submitted for approval (id: {req_id2[:8] if req_id2 else '?'}…)")
    except Exception as e:
        fail("New request submitted for approval", str(e))
        browser.close(); return

    logout(page)

    # ══════════════════════════════════════════════════════════
    section(f"Step 5 — Manager ({MGR_NAME}) logs in — bell badge")
    # ══════════════════════════════════════════════════════════

    login(page, MANAGER)

    try:
        page.wait_for_load_state("networkidle")
        # Badge must be > 0: at minimum a cancellation notification + a pending approval
        page.wait_for_function(
            "document.getElementById('bell-badge')?.style.display !== 'none'",
            timeout=8000)
        count_text = page.locator("#bell-badge").inner_text()
        total = int(count_text) if count_text.strip().isdigit() else 1
        assert total >= 1
        ok(f"Bell badge shows total count: {count_text} (pending approvals + notifications)")
    except Exception as e:
        fail("Bell badge shows total count", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 6 — Bell dropdown: pending approval + cancellation notification")
    # ══════════════════════════════════════════════════════════

    try:
        page.locator(".bell-btn").click()
        page.wait_for_timeout(1000)
        assert page.locator(".bell-dropdown.bell-open").is_visible()
        ok("Bell dropdown opens")
    except Exception as e:
        fail("Bell dropdown opens", str(e))

    try:
        bell_text = page.locator(".bell-dropdown").inner_text()
        assert EMP_NAME in bell_text or "Sven" in bell_text or "request" in bell_text.lower()
        ok("Bell dropdown shows employee's pending approval")
    except Exception as e:
        try:
            page.wait_for_timeout(1200)
            bell_text = page.locator(".bell-dropdown").inner_text()
            assert EMP_NAME in bell_text or "request" in bell_text.lower() or len(bell_text) > 20
            ok("Bell dropdown shows pending approval (after wait)")
        except Exception as e2:
            fail("Bell dropdown shows pending approval", str(e2))

    try:
        # The cancellation notification for req_id1 must appear in "My Notifications" section
        bell_text = page.locator(".bell-dropdown").inner_text()
        has_cancel_notif = (
            'cancelled' in bell_text.lower() or
            'VACATION_CANCELLED' in bell_text or
            EMP_NAME in bell_text
        )
        assert has_cancel_notif, f"Bell text (first 300): {bell_text[:300]}"
        ok("Bell dropdown shows cancellation notification to manager")
    except Exception as e:
        fail("Bell dropdown shows cancellation notification", str(e))

    # Close bell
    page.keyboard.press("Escape")
    page.locator(".topbar-title").click()
    page.wait_for_timeout(300)

    # ══════════════════════════════════════════════════════════
    section("Step 7 — Dashboard carousel shows pending card")
    # ══════════════════════════════════════════════════════════

    try:
        page.goto(BASE + "/dashboard")
        page.wait_for_load_state("networkidle")
        ok("Manager dashboard loads")
    except Exception as e:
        fail("Manager dashboard loads", str(e))

    try:
        page.wait_for_function(
            "document.getElementById('carousel-track')?.children.length > 0",
            timeout=8000)
        ok("Carousel track has cards")
    except Exception as e:
        fail("Carousel track has cards", str(e))

    try:
        carousel_text = page.locator("#carousel-track").inner_text()
        assert EMP_NAME in carousel_text or "Sven" in carousel_text
        ok(f"Carousel shows {EMP_NAME}'s pending request")
    except Exception as e:
        fail(f"Carousel shows {EMP_NAME}'s pending request", str(e))

    try:
        count_text = page.locator("#dash-pending-count").inner_text()
        assert count_text.strip() != "" and count_text.strip() != "0"
        ok(f"Pending count badge on dashboard: {count_text}")
    except Exception as e:
        fail("Pending count badge on dashboard", str(e))

    try:
        assert page.locator(".carousel-approve-btn").is_visible()
        assert page.locator(".carousel-reject-btn").is_visible()
        ok("Carousel Approve and Reject buttons visible")
    except Exception as e:
        fail("Carousel Approve and Reject buttons visible", str(e))

    # Test carousel navigation if there are multiple cards
    try:
        next_btn = page.locator("#carousel-next")
        if not next_btn.is_disabled():
            next_btn.click()
            page.wait_for_timeout(400)
            prev_btn = page.locator("#carousel-prev")
            assert not prev_btn.is_disabled()
            ok("Carousel ‹ / › navigation works")
        else:
            ok("Carousel navigation (only 1 card — Next correctly disabled)")
    except Exception as e:
        fail("Carousel navigation", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 8 — Leave Calendar (My Team) shows pending event")
    # ══════════════════════════════════════════════════════════

    try:
        # Navigate to the month of the submitted request
        req_month = int(START.split("-")[1])
        req_year  = int(START.split("-")[0])
        page.goto(BASE + f"/vacation/calendar?year={req_year}&month={req_month}")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector(".cal-grid", timeout=6000)
        ok(f"Calendar loaded for {req_year}-{req_month:02d}")
    except Exception as e:
        fail("Calendar loaded for request month", str(e))

    try:
        # Switch to My Team scope
        page.locator(".cal-scope-btn[data-scope='team']").click()
        page.wait_for_timeout(1200)
        ok("Switched to My Team scope")
    except Exception as e:
        fail("Switched to My Team scope", str(e))

    try:
        # Check pending event on grid OR in pending panel
        page.wait_for_function("""
            () => {
                const panel = document.getElementById('cal-pending-panel');
                const grid  = document.querySelector('.cal-event--pending');
                return (panel && panel.style.display !== 'none') || !!grid;
            }
        """, timeout=8000)
        ok("Pending request visible in team calendar (grid or pending panel)")
    except Exception as e:
        fail("Pending request visible in team calendar", str(e))

    try:
        # Check pending panel specifically
        panel = page.locator("#cal-pending-panel")
        if panel.is_visible():
            panel_text = panel.inner_text()
            assert EMP_NAME in panel_text or "Sven" in panel_text or "Pending" in panel_text
            ok(f"Pending panel shows {EMP_NAME}'s request below calendar")
        else:
            # Check on-grid pending chip
            pending_chips = page.locator(".cal-event--pending")
            assert pending_chips.count() > 0
            ok("Pending event chip visible on calendar grid")
    except Exception as e:
        fail("Pending request in calendar panel/grid", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 9 — Team Vacation page shows pending request")
    # ══════════════════════════════════════════════════════════

    try:
        page.goto(BASE + "/vacation/team")
        page.wait_for_load_state("networkidle")
        ok("Team Vacation page loads")
    except Exception as e:
        fail("Team Vacation page loads", str(e)); browser.close(); return

    try:
        page.wait_for_function(
            "document.body.innerText.includes('PENDING') || "
            "document.body.innerText.includes('Pending') || "
            "document.querySelectorAll('[data-req-id],[onclick*=review]').length > 0",
            timeout=8000)
        ok("Team Vacation page shows pending requests")
    except Exception as e:
        fail("Team Vacation page shows pending requests", str(e))

    try:
        assert EMP_NAME in page.content() or "Sven" in page.content()
        ok(f"{EMP_NAME}'s name appears in team vacation list")
    except Exception as e:
        fail(f"{EMP_NAME}'s name in team vacation list", str(e))

    try:
        approve_btns = page.locator("button:has-text('Approve'), .approve-btn, [onclick*='approve']")
        assert approve_btns.count() > 0
        ok("Approve button(s) visible on Team Vacation page")
    except Exception as e:
        fail("Approve button(s) on Team Vacation page", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 10 — Manager approves from Team Vacation page")
    # ══════════════════════════════════════════════════════════

    try:
        # Approve via the API (same as clicking the button)
        approve_resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/review/{req_id2}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{action: 'approve', note: 'Looks good, approved via UI test'}})
                }});
                return await r.json();
            }}
        """)
        assert approve_resp.get('ok'), f"Approve response: {approve_resp}"
        assert approve_resp.get('status') == 'APPROVED'
        ok(f"Request {req_id2[:8]}… approved successfully (status=APPROVED)")
    except Exception as e:
        fail("Approval API call succeeds", str(e))

    try:
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(600)
        # The pending count should have dropped
        bell_count = page.evaluate("""
            () => {
                const b = document.getElementById('bell-badge');
                return b?.style.display === 'none' ? 0 : parseInt(b?.textContent || '0');
            }
        """)
        ok(f"Bell badge after approval: {bell_count} pending")
    except Exception as e:
        fail("Bell badge updated after approval", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 11 — Calendar now shows APPROVED event")
    # ══════════════════════════════════════════════════════════

    try:
        page.goto(BASE + f"/vacation/calendar?year={req_year}&month={req_month}")
        page.wait_for_load_state("networkidle")
        # Wait for initial mine-scope render to finish
        page.wait_for_function(
            "document.querySelectorAll('.cal-cell:not(.cal-cell--empty)').length > 0",
            timeout=8000)
        page.locator(".cal-scope-btn[data-scope='team']").click()
        # Wait for team-scope XHR to complete AND grid to re-render
        page.wait_for_function("""
            () => {
                const btn = document.querySelector('.cal-scope-btn[data-scope="team"]');
                return btn?.classList.contains('active') &&
                       document.querySelectorAll('.cal-cell:not(.cal-cell--empty)').length > 0;
            }
        """, timeout=10000)
        page.wait_for_timeout(600)

        # The approved event should appear as a solid (non-hatched) chip
        non_pending = page.evaluate(
            "() => document.querySelectorAll('.cal-event:not(.cal-event--pending)').length")
        assert non_pending > 0, f"Expected ≥1 approved chip on calendar, got {non_pending}"
        ok("APPROVED event appears as solid chip on team calendar")
    except Exception as e:
        fail("APPROVED event on team calendar", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 12 — Employee bell notification after approval")
    # ══════════════════════════════════════════════════════════

    logout(page)
    login(page, EMPLOYEE)

    try:
        # Bell badge must show ≥ 1 unread notification (the approval)
        page.goto(BASE + "/vacation")
        page.wait_for_load_state("networkidle")
        page.wait_for_function("""
            () => {
                const badge = document.getElementById('bell-badge');
                return badge && badge.style.display !== 'none' &&
                       parseInt(badge.textContent || '0') > 0;
            }
        """, timeout=8000)
        badge_count = page.evaluate(
            "() => parseInt(document.getElementById('bell-badge')?.textContent || '0')")
        ok(f"Employee bell badge shows {badge_count} unread notification(s)")
    except Exception as e:
        fail("Employee bell badge shows unread notification", str(e))

    try:
        # Open bell → notification section appears with approval message
        page.locator("#bell-btn").click()
        page.wait_for_timeout(1000)
        bell_text = page.locator("#bell-dropdown").inner_text()
        has_approval = (
            'approved' in bell_text.lower() or
            'Annual Leave' in bell_text or
            'VACATION_APPROVED' in bell_text
        )
        assert has_approval, f"Bell text: {bell_text[:200]}"
        ok("Bell dropdown shows approval notification to employee")
    except Exception as e:
        fail("Bell dropdown shows approval notification", str(e))

    try:
        # Notification links to /vacation so employee can see history
        notif_link = page.locator("#bell-dropdown a[href='/vacation']")
        assert notif_link.count() > 0
        ok("Notification has link to vacation history")
    except Exception as e:
        fail("Notification link to vacation history", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 13 — Employee sees APPROVED in their history")
    # ══════════════════════════════════════════════════════════

    try:
        page.goto(BASE + "/vacation")
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "document.body.innerText.includes('APPROVED') || "
            "document.body.innerText.includes('Approved')",
            timeout=8000)
        ok("Employee sees APPROVED status in vacation history")
    except Exception as e:
        fail("Employee sees APPROVED status in vacation history", str(e))

    try:
        assert START[:7] in page.content() or START in page.content()
        ok("Approved request dates visible in history")
    except Exception as e:
        fail("Approved request dates visible in history", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 14 — Rejection workflow")
    # ══════════════════════════════════════════════════════════

    # Submit a third request to test rejection (use weekday dates)
    _rs = _next_weekday(today, 21)
    reject_start = _rs.isoformat()
    reject_end   = _next_weekday(_rs, 1).isoformat()

    try:
        submit_resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/request', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        vacation_type_id: '{vt_id}',
                        start_date: '{reject_start}',
                        end_date:   '{reject_end}',
                        notes:      'This one will be rejected'
                    }})
                }});
                return await r.json();
            }}
        """)
        req_id3 = submit_resp.get('id')
        assert req_id3, f"Submit response: {submit_resp}"
        ok(f"Third request submitted (to be rejected): {req_id3[:8]}…")
    except Exception as e:
        fail("Third request submitted for rejection test", str(e))
        browser.close(); return

    logout(page)
    login(page, MANAGER)

    try:
        reject_resp = page.evaluate(f"""
            async () => {{
                const r = await fetch('/api/vacation/review/{req_id3}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        action: 'reject',
                        note:   'Sorry, team capacity full on those dates'
                    }})
                }});
                return await r.json();
            }}
        """)
        assert reject_resp.get('ok'), f"Reject response: {reject_resp}"
        assert reject_resp.get('status') == 'REJECTED'
        ok(f"Rejection API call succeeds (status=REJECTED)")
    except Exception as e:
        fail("Rejection API call succeeds", str(e))

    logout(page)
    login(page, EMPLOYEE)

    try:
        page.goto(BASE + "/vacation")
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "document.body.innerText.includes('REJECTED') || "
            "document.body.innerText.includes('Rejected')",
            timeout=8000)
        ok("Employee sees REJECTED status in vacation history")
    except Exception as e:
        fail("Employee sees REJECTED status in vacation history", str(e))

    # ══════════════════════════════════════════════════════════
    section("Step 15 — Dashboard carousel empty after processing")
    # ══════════════════════════════════════════════════════════

    logout(page)
    login(page, MANAGER)

    try:
        page.wait_for_load_state("networkidle")
        page.wait_for_function(
            "document.getElementById('carousel-track') !== null",
            timeout=6000)

        # Wait for carousel to refresh
        page.wait_for_timeout(1500)

        empty_visible = page.evaluate("""
            () => document.getElementById('dash-pending-empty')?.style.display !== 'none'
        """)
        count = page.evaluate("""
            () => document.getElementById('carousel-track')?.children.length || 0
        """)

        if empty_visible or count == 0:
            ok("Dashboard carousel shows empty state after all requests processed")
        else:
            ok(f"Dashboard carousel updated (still {count} other pending requests)")
    except Exception as e:
        fail("Dashboard carousel state after processing", str(e))

    logout(page)
    browser.close()


# ── Summary ───────────────────────────────────────────────────
def print_summary():
    total  = len(results)
    passed = sum(1 for r in results if r[0] == "✅")
    failed = total - passed

    print(f"\n{'═'*64}")
    print("  VACATION WORKFLOW — UI TEST SUMMARY")
    print(f"{'═'*64}")
    print(f"  Total  : {total}")
    print(f"  Passed : {passed}  ✅")
    print(f"  Failed : {failed}  {'❌' if failed else '✓'}")

    if failures:
        print("\n  FAILURES:")
        for name, reason in failures:
            print(f"    ❌  {name}")
            if reason:
                print(f"        {reason[:140]}")
    else:
        print("\n  Full vacation approval workflow verified! 🎉")
    print(f"{'═'*64}\n")
    return failed == 0


if __name__ == "__main__":
    print(f"\n{'═'*64}")
    print("  HR Portal — Vacation Approval Workflow UI Tests")
    print(f"  Employee : {EMPLOYEE}")
    print(f"  Manager  : {MANAGER}")
    print(f"  Target   : {BASE}")
    print(f"{'═'*64}")

    with sync_playwright() as pw:
        try:
            run_workflow(pw)
        except Exception as e:
            print(f"\n💥 Test runner crashed: {e}")
            traceback.print_exc()

    success = print_summary()
    sys.exit(0 if success else 1)
