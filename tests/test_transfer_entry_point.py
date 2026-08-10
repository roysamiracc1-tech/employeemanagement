"""KAN-185 — the HR-initiated transfer entry point: anti-bypass suite.

A transfer **is** an org change (EP38 technical design §4.3): the Transfer… entry
point and the org-tree drag-and-drop post to the same `POST /api/org-change/request`
and the same `org_change_service.create_request()`. There is no second engine, no
second table and no second feature code.

The risk in this story is therefore not building it — it is someone building a
**second path**. This suite exists to make that impossible to do quietly. It
asserts, for the transfer entry point specifically:

* nothing is applied at creation time, and nothing before the FINAL approval;
* an employee can never initiate their own move, and the feature gate alone is
  never what stops them;
* approvals stay strictly sequential and one rejection applies nothing;
* every read and write is company-scoped, and a foreign UUID posted straight at
  the API is refused;
* the resulting request and approval chain are **identical** to the ones the
  drag-and-drop path produces.

All DB interaction is mocked; data is synthetic.
"""
import json

import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import _set_session, FakeTransaction, SAMPLE_EMPLOYEE


# ── Synthetic fixtures ────────────────────────────────────────────────────────

CO       = 'co-1'
OTHER_CO = 'co-2'

SUBJECT           = {'company_id': CO, 'employment_status': 'ACTIVE', 'name': 'Sub Ject'}
MANAGER           = {'company_id': CO, 'employment_status': 'ACTIVE'}
CURRENT_PLACEMENT = {'bu': 'bu-cur', 'fu': 'fu-cur', 'loc': 'loc-cur',
                     'cc': 'cc-1', 'mgr': 'm-old'}

# A two-level chain, so "nothing applies before the last level" is observable.
STEP_1 = {'step_order': 1, 'approver_type': 'ROLE', 'approver_role': 'HR_ADMIN',
          'approver_employee_id': None, 'label': 'HR approval'}
STEP_2 = {'step_order': 2, 'approver_type': 'ROLE', 'approver_role': 'PORTAL_ADMIN',
          'approver_employee_id': None, 'label': 'Portal approval'}

# The profile page's view of the subject — the full `fetch_employees` shape, so
# the page renders on its own terms and these tests only vary what they mean to.
PROFILE_EMPLOYEE = dict(SAMPLE_EMPLOYEE, id='emp-sub', employee_number='EMP-0142',
                        full_name='Sub Ject', first_name='Sub', last_name='Ject',
                        employment_status='ACTIVE')

HR_USER     = {'user_id': 'u-hr', 'employee_id': 'emp-hr', 'company_id': CO,
               'roles': ['HR_ADMIN']}
PORTAL_USER = {'user_id': 'u-pa', 'employee_id': 'emp-pa', 'company_id': CO,
               'roles': ['PORTAL_ADMIN']}


def _norm(sql):
    return ' '.join(str(sql).split())


def route_query(*, subject=SUBJECT, manager=MANAGER, unit_in_company=True,
                cycle=False, pending=None, business_units=(), functional_units=(),
                locations=(), managers=(), direct_reports=0):
    """Stub for `app.routes.org_change.query`, dispatching on the SQL.

    Order-independent on purpose: the route's guards may be reordered without
    silently turning these tests into assertions about something else.
    """
    def _q(sql, params=(), one=False):
        s = _norm(sql)
        if 'WITH RECURSIVE' in s:                       # _would_create_cycle
            return {'ok': 1} if cycle else None
        if 'org_change_requests' in s:                  # _pending_request_for
            return {'id': pending} if pending else None
        if 'manager_relationships' in s:                # prefill direct-report count
            return {'c': direct_reports}
        if 'business_units' in s:
            return ({'ok': 1} if unit_in_company else None) if one else list(business_units)
        if 'functional_units' in s:
            return ({'ok': 1} if unit_in_company else None) if one else list(functional_units)
        if 'locations' in s:
            return ({'ok': 1} if unit_in_company else None) if one else list(locations)
        if 'FROM employees' in s:
            if not one:
                return list(managers)                   # prefill manager options
            if 'first_name' in s:
                return dict(subject) if subject else None
            return dict(manager) if manager else None
        return None
    return _q


@pytest.fixture
def employee_client(client):
    """A plain employee — the person a transfer would be *about*."""
    _set_session(client, roles=['EMPLOYEE'], employee_id='emp-sub', user_id='u-emp')
    return client


@pytest.fixture
def lead_client(client):
    _set_session(client, roles=['SOLID_LINE_MANAGER', 'EMPLOYEE'],
                 employee_id='emp-lead', user_id='u-lead')
    return client


@pytest.fixture
def hr_client(client):
    _set_session(client, roles=['HR_ADMIN', 'EMPLOYEE'],
                 employee_id='emp-hr', user_id='u-hr')
    return client


def _post(client, payload, **stub):
    """POST a transfer through the one creation path, with the DB stubbed."""
    mk = MagicMock(return_value='req-new')
    with patch('app.auth.can_access_feature', return_value=True), \
         patch('app.routes.org_change.query', side_effect=route_query(**stub)), \
         patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
         patch('app.routes.org_change.svc.create_request', mk):
        res = client.post('/api/org-change/request', data=json.dumps(payload),
                          content_type='application/json')
    return res, mk


TRANSFER = {'employee_id': 'emp-sub', 'manager_id': 'm-new', 'business_unit_id': 'bu-new',
            'functional_unit_id': None, 'location_id': None, 'reason': 'Team realignment'}


# ── 0. The profile entry point (UX spec §6.1) ─────────────────────────────────

class TestProfileEntryPoint:
    """The Transfer… affordance and its four display gates.

    These assert the *display* layer only. Hiding the button is never what stops
    a move — every case here is independently refused by the API in §2/§4/§6 —
    but an entry point that appears where it must not is still a defect.
    """

    def _profile(self, client, emp_id, employee=None, feature=True, manages=True):
        emp = dict(PROFILE_EMPLOYEE, **(employee or {}))
        with patch('app.routes.employees.fetch_employees', return_value=[emp]), \
             patch('app.routes.employees.query', return_value=[]), \
             patch('app.routes.employees.can_access_feature', return_value=feature), \
             patch('app.auth.can_access_feature', return_value=feature), \
             patch('app.routes.employees.direct_report_ids', return_value=[]), \
             patch('app.routes.employees.is_direct_report', return_value=manages), \
             patch('app.routes.org_change.employee_solid_manager',
                   return_value='emp-lead' if manages else 'someone-else'):
            res = client.get(f'/profile/{emp_id}')
        return res, res.data.decode()

    def test_hr_sees_the_entry_point_on_someone_elses_profile(self, hr_client):
        res, html = self._profile(hr_client, 'emp-sub')
        assert res.status_code == 200
        assert 'openTransferModal(' in html
        assert 'Transfer…' in html

    def test_the_handler_attribute_survives_quotes_in_a_name(self, hr_client):
        """The button must still be a button for O'Brien and for a "nickname".

        Regression: the handler was built in a double-quoted attribute from
        `| tojson`, which escapes `'` but leaves `"` intact — so a quote in a
        name terminated the attribute and the browser parsed the rest as junk
        attributes. The button rendered and the substring was present, so a
        naive `'openTransferModal(' in html` check passed while the control was
        dead. This parses the tag instead.
        """
        from html.parser import HTMLParser

        tricky = 'Ann "Anni" O\'Brien-<script>'
        _, html = self._profile(hr_client, 'emp-sub', employee={'full_name': tricky})

        class Grab(HTMLParser):
            onclick = None
            extra = None

            def handle_starttag(self, tag, attrs):
                d = dict(attrs)
                if tag == 'button' and 'openTransferModal' in (d.get('onclick') or ''):
                    Grab.onclick = d['onclick']
                    # Anything beyond these four means the attribute broke apart.
                    Grab.extra = set(d) - {'onclick', 'type', 'class', 'aria-haspopup'}

        Grab().feed(html)
        assert Grab.onclick, 'the Transfer… handler did not survive parsing'
        assert not Grab.extra, f'the handler attribute broke apart: {Grab.extra}'
        # The three arguments are JSON literals, so they decode back to exactly
        # what was passed in — quotes escaped on the wire, intact at the opener.
        args = json.loads('[%s]' % Grab.onclick[len('openTransferModal('):-1])
        assert args == ['emp-sub', tricky, 'EMP-0142']
        # …and the name never lands in the page as live markup.
        assert 'Brien-<script>' not in html

    def test_the_shared_dialog_ships_with_the_entry_point(self, hr_client):
        """One dialog component, not a profile-local copy (UX spec §6.0)."""
        _, html = self._profile(hr_client, 'emp-sub')
        assert 'id="move-modal"' in html
        assert 'Request Position Change' in html, 'the dialog must not say "Transfer"'

    def test_no_entry_point_on_your_own_profile(self, hr_client):
        """P3 — an admin may transfer anyone via the API, but not from here."""
        res, html = self._profile(hr_client, 'emp-hr',
                                  employee={'id': 'emp-hr'})
        assert res.status_code == 200
        assert 'openTransferModal(' not in html
        # The dialog is not shipped either — nothing can open it.
        assert 'id="move-modal"' not in html

    def test_no_entry_point_without_org_change_write(self, hr_client):
        """P1 — the feature gate, not a role list."""
        _, html = self._profile(hr_client, 'emp-sub', feature=False)
        assert 'openTransferModal(' not in html

    def test_no_entry_point_for_someone_who_may_view_but_not_initiate(self, client):
        """P2 — the display helper mirrors `_can_initiate_for`, not view access.

        A DEPARTMENT_HEAD is the case that matters: they can open anyone's
        profile in their scope, but they are neither the subject's solid-line
        manager nor an HR/Portal/System admin, so they may not move them. (A
        plain SOLID_LINE_MANAGER outside the line cannot even reach the page,
        so it proves nothing about this gate.)
        """
        _set_session(client, roles=['DEPARTMENT_HEAD', 'EMPLOYEE'],
                     employee_id='emp-head', user_id='u-head')
        res, html = self._profile(client, 'emp-sub', manages=False)
        assert res.status_code == 200, 'a department head must still see the profile'
        assert 'Sub Ject' in html
        assert 'openTransferModal(' not in html

    def test_entry_point_for_a_manager_of_their_own_report(self, lead_client):
        _, html = self._profile(lead_client, 'emp-sub', manages=True)
        assert 'openTransferModal(' in html

    def test_no_entry_point_for_a_former_employee(self, hr_client):
        """AC-185-12 at the display layer — KAN-184 is about to make this real."""
        _, html = self._profile(hr_client, 'emp-sub',
                                employee={'employment_status': 'TERMINATED'})
        assert 'openTransferModal(' not in html

    def test_the_gate_is_the_shared_rule_not_a_copy_of_it(self):
        """CLAUDE.md invariant 2 — one implementation of the initiator rule."""
        import inspect
        from app.routes import employees as mod
        src = inspect.getsource(mod._can_transfer)
        assert 'can_initiate_org_change_for' in src
        assert 'employee_solid_manager' not in src, 'the rule was re-implemented'
        assert "can_access_feature('org_change', 'w')" in src
        assert 'require_roles' not in src


# ── 0b. The directory row entry point (UX spec §6.1.2, AC-185-01) ─────────────

class TestDirectoryEntryPoint:
    """Rows are rendered client-side, so the gate is the pair of flags the
    server hands the page. These pin those flags, not the JS."""

    def _directory(self, client, feature=True):
        with patch('app.routes.employees.query', return_value=[]), \
             patch('app.routes.employees.can_access_feature', return_value=feature), \
             patch('app.auth.can_access_feature', return_value=feature), \
             patch('app.routes.employees.current_company_id', return_value=CO):
            res = client.get('/directory')
        return res, res.data.decode()

    def test_hr_gets_the_row_menu_and_the_shared_dialog(self, hr_client):
        res, html = self._directory(hr_client)
        assert res.status_code == 200
        assert 'const DIR_ACTIONS      = true' in html
        assert 'const CAN_TRANSFER_ANY = true' in html
        assert 'id="move-modal"' in html, 'the row action has no dialog to open'

    def test_a_head_may_only_transfer_their_own_reports(self, client):
        """The row rule falls back to `solid_manager_id == viewer` for non-admins."""
        _set_session(client, roles=['DEPARTMENT_HEAD', 'EMPLOYEE'],
                     employee_id='emp-head', user_id='u-head')
        _, html = self._directory(client)
        assert 'const DIR_ACTIONS      = true' in html
        assert 'const CAN_TRANSFER_ANY = false' in html, (
            'a department head must not get a Transfer action on every row')
        assert '"emp-head"' in html, 'the viewer id the per-row rule compares against'

    def test_no_row_menu_without_org_change_write(self, hr_client):
        """P1 — the feature gate, not the directory's own role list."""
        _, html = self._directory(hr_client, feature=False)
        assert 'const DIR_ACTIONS      = false' in html
        assert 'id="move-modal"' not in html

    def test_the_actions_column_and_the_colspan_agree(self, hr_client):
        """One flag drives header, rows and empty state — they cannot diverge."""
        _, html = self._directory(hr_client)
        assert '<th><span class="sr-only">Actions</span></th>' in html
        assert 'colspan="12"' in html
        assert 'DIR_ACTIONS ? 12 : 11' in html

    def test_the_column_is_absent_when_the_action_is(self, hr_client):
        _, html = self._directory(hr_client, feature=False)
        assert 'sr-only">Actions' not in html
        assert 'colspan="11"' in html

    def test_the_admin_role_set_is_defined_in_exactly_one_place(self):
        """CLAUDE.md invariant 2 — the initiator rule has one implementation.

        The directory needs the "may initiate for anyone" half of the rule
        without a per-row manager lookup, which is a standing temptation to
        re-list HR_ADMIN/PORTAL_ADMIN/SYSTEM_ADMIN here. It must borrow instead.
        """
        import inspect
        from app.routes import employees as mod
        # Body only — the `@require_roles` above it is the directory's own
        # page-access gate, a separate pre-existing concern (KAN-182), not the
        # org-change initiator rule this test is about.
        body = ''.join(l for l in inspect.getsource(mod.directory).splitlines(True)
                       if not l.lstrip().startswith('@'))
        assert 'can_initiate_org_change_for_anyone' in body
        assert 'HR_ADMIN' not in body, 'the initiator admin set was re-listed'
        assert 'PORTAL_ADMIN' not in body


# ── 1. No second write path ───────────────────────────────────────────────────

class TestNoSecondWritePath:
    """T-185-4 as an executable gate, not just a review convention."""

    def test_route_module_never_writes_to_the_database(self):
        import inspect
        from app.routes import org_change as mod
        src = inspect.getsource(mod).upper()
        for forbidden in ('INSERT INTO', 'UPDATE EMPLOYEE', 'UPDATE ORG_CHANGE',
                          'DELETE FROM'):
            assert forbidden not in src, (
                f'{forbidden} in app/routes/org_change.py — the org-change engine is '
                f'the only writer of these tables (CLAUDE.md invariant 5)')

    def test_route_module_cannot_write_even_by_accident(self):
        from app.routes import org_change as mod
        # `execute` / `insert_returning` are deliberately not imported here.
        assert not hasattr(mod, 'execute')
        assert not hasattr(mod, 'insert_returning')

    def test_creation_never_touches_placement_tables(self):
        from app.routes import org_change as mod
        src = mod.api_org_change_request.__doc__ or ''
        assert 'Nothing is applied here' in src
        res, mk = _post(_client_hr(), TRANSFER)
        assert res.status_code == 200
        mk.assert_called_once()

    def test_feature_gate_is_declarative_not_a_role_list(self):
        import inspect
        from app.routes import org_change as mod
        src = inspect.getsource(mod)
        assert "@require_feature_access('org_change', 'w')" in src
        # CLAUDE.md: hardcoded role lists on feature routes are forbidden.
        assert '@require_roles(' not in src


def _client_hr():
    from app import app as flask_app
    c = flask_app.test_client()
    _set_session(c, roles=['HR_ADMIN', 'EMPLOYEE'], employee_id='emp-hr', user_id='u-hr')
    return c


# ── 2. The initiator rule (CLAUDE.md org-change invariant 2) ──────────────────

class TestCannotInitiateOwnMove:
    def test_employee_cannot_transfer_themselves_even_with_the_feature_granted(
            self, employee_client):
        """The feature flag alone must NOT be sufficient — AC-185-02.

        Still a 403, but since KAN-203 it is refused by the **self** guard ahead
        of the manager rule, so the message names the real reason instead of
        talking about "your own reports" when the report in question is you.
        """
        with patch('app.routes.org_change.employee_solid_manager',
                   return_value='their-boss'), \
             patch('app.routes.org_change.audit_service'):
            res, mk = _post(employee_client,
                            dict(TRANSFER, employee_id='emp-sub'))  # emp-sub IS the caller
        assert res.status_code == 403
        assert 'yourself' in json.loads(res.data)['error']
        mk.assert_not_called()

    def test_employee_cannot_transfer_anyone_else_either(self, employee_client):
        with patch('app.routes.org_change.employee_solid_manager', return_value='someone'):
            res, mk = _post(employee_client, dict(TRANSFER, employee_id='emp-other'))
        assert res.status_code == 403
        mk.assert_not_called()

    def test_manager_cannot_transfer_themselves(self, lead_client):
        """A manager is not their own solid-line manager, so the rule refuses it."""
        with patch('app.routes.org_change.employee_solid_manager', return_value='their-boss'):
            res, mk = _post(lead_client, dict(TRANSFER, employee_id='emp-lead'))
        assert res.status_code == 403
        mk.assert_not_called()

    def test_manager_may_transfer_a_direct_report(self, lead_client):
        with patch('app.routes.org_change.employee_solid_manager', return_value='emp-lead'):
            res, mk = _post(lead_client, TRANSFER)
        assert res.status_code == 200
        mk.assert_called_once()

    def test_manager_may_not_transfer_someone_elses_report(self, lead_client):
        with patch('app.routes.org_change.employee_solid_manager', return_value='another-lead'):
            res, mk = _post(lead_client, TRANSFER)
        assert res.status_code == 403
        mk.assert_not_called()

    def test_display_helper_mirrors_the_server_rule(self, lead_client):
        """`can_initiate_org_change_for` must never be more permissive than the API."""
        from app.routes.org_change import can_initiate_org_change_for
        with lead_client.application.test_request_context('/'):
            from flask import session as flask_session
            flask_session['employee_id'] = 'emp-lead'
            flask_session['user_id'] = 'u-lead'
            flask_session['roles'] = ['SOLID_LINE_MANAGER']
            with patch('app.routes.org_change.employee_solid_manager', return_value='emp-lead'):
                assert can_initiate_org_change_for('emp-sub') is True
            with patch('app.routes.org_change.employee_solid_manager', return_value='other'):
                assert can_initiate_org_change_for('emp-sub') is False

    def test_hr_admin_cannot_transfer_themselves_either(self, hr_client):
        """INVERTED BY KAN-203 — and this test's previous docstring predicted it.

        It used to assert that HR/Portal/System admins may initiate for anyone
        *including themselves*, pinning the documented rule while explicitly
        flagging the open question: *"if the rule is meant to be 'nobody, ever,
        at any privilege level', it changes `_can_initiate_for`, which is a
        CLAUDE.md invariant and not this ticket's to redefine."*

        KAN-203 is the ticket that redefined it. The admin exemption exists so HR
        can move **other people**; combined with `decide()` having no self-check,
        the old behaviour let an HR_ADMIN raise their own move and then approve
        it. The assertion is inverted rather than deleted so the trail from the
        old rule to the new one survives in the suite.
        """
        with patch('app.routes.org_change.audit_service'):
            res, mk = _post(hr_client, dict(TRANSFER, employee_id='emp-hr'))
        assert res.status_code == 403
        assert 'yourself' in json.loads(res.data)['error']
        mk.assert_not_called()


# ── 3. Nothing is applied without the full chain ──────────────────────────────

class TestNothingAppliesEarly:
    def _decide(self, current_step, total, user, decision, chain_len=2):
        """Drive `decide()` with the DB mocked; report whether the move applied."""
        from app.services import org_change_service as svc
        req = {'id': 'req-1', 'company_id': CO, 'employee_id': 'emp-sub',
               'requested_by_user_id': 'u-hr', 'current_step': current_step,
               'status': 'PENDING', 'proposed_manager_id': 'm-new'}
        step = STEP_1 if current_step == 1 else STEP_2
        rows = [req, step, {'n': 'Sub Ject'}]
        if decision == 'approve':
            rows.append({'c': total})
            if current_step < total:
                rows.append(STEP_2)
        rows.append([{'id': 'u-sub'}])
        applied = []
        with patch.object(svc, 'query', side_effect=rows), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'execute'), \
             patch.object(svc, '_apply_change', side_effect=lambda rid: applied.append(rid)), \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-pa']), \
             patch.object(svc, 'notif'):
            ok, status = svc.decide('req-1', user, decision, None)
        return ok, status, applied

    def test_creation_applies_nothing(self):
        """A submitted transfer only opens a PENDING request."""
        from app.services import org_change_service as svc
        with patch.object(svc, 'current_placement', return_value=CURRENT_PLACEMENT), \
             patch.object(svc, 'workflow_steps', return_value=[STEP_1, STEP_2]), \
             patch.object(svc, 'query', return_value=None), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'insert_returning', return_value={'id': 'req-1'}) as ins, \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, '_apply_change') as apply_mock, \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-hr']), \
             patch.object(svc, '_emp_name', return_value='Sub Ject'), \
             patch.object(svc, 'notif'):
            svc.create_request(CO, 'emp-sub', 'u-hr',
                               {'business_unit_id': 'bu-new', 'functional_unit_id': None,
                                'location_id': None, 'manager_id': 'm-new'}, 'Realignment')
        apply_mock.assert_not_called()
        sql = _norm(ins.call_args.args[0])
        assert "'PENDING'" in sql and 'org_change_requests' in sql
        writes = ' '.join(_norm(c.args[0]) for c in exe.call_args_list)
        assert 'org_change_approvals' in writes
        # No placement table is touched at creation time.
        assert 'employee_org_assignments' not in writes
        assert 'manager_relationships' not in writes

    def test_first_of_two_approvals_applies_nothing(self):
        ok, status, applied = self._decide(1, 2, HR_USER, 'approve')
        assert ok and status == 'PENDING'
        assert applied == [], 'the move was applied before the final approval'

    def test_only_the_final_approval_applies(self):
        ok, status, applied = self._decide(2, 2, PORTAL_USER, 'approve')
        assert ok and status == 'APPROVED'
        assert applied == ['req-1']

    def test_a_single_rejection_stops_the_chain_and_applies_nothing(self):
        ok, status, applied = self._decide(1, 2, HR_USER, 'reject')
        assert ok and status == 'REJECTED'
        assert applied == []

    def test_rejection_at_the_last_level_applies_nothing(self):
        ok, status, applied = self._decide(2, 2, PORTAL_USER, 'reject')
        assert ok and status == 'REJECTED'
        assert applied == []

    def test_approvals_are_strictly_sequential(self):
        """A level-2 approver cannot decide while the request sits at level 1."""
        from app.services import org_change_service as svc
        req = {'id': 'req-1', 'company_id': CO, 'employee_id': 'emp-sub',
               'requested_by_user_id': 'u-hr', 'current_step': 1, 'status': 'PENDING',
               'proposed_manager_id': 'm-new'}
        with patch.object(svc, 'query', side_effect=[req, STEP_1]), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, '_apply_change') as apply_mock:
            ok, msg = svc.decide('req-1', PORTAL_USER, 'approve', None)
        assert ok is False and 'approver for this step' in msg
        exe.assert_not_called()
        apply_mock.assert_not_called()

    def test_a_decided_request_cannot_be_decided_again(self):
        from app.services import org_change_service as svc
        req = {'id': 'req-1', 'company_id': CO, 'employee_id': 'emp-sub',
               'requested_by_user_id': 'u-hr', 'current_step': 2, 'status': 'REJECTED',
               'proposed_manager_id': 'm-new'}
        with patch.object(svc, 'query', side_effect=[req]), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, '_apply_change') as apply_mock:
            ok, msg = svc.decide('req-1', PORTAL_USER, 'approve', None)
        assert ok is False and 'no longer pending' in msg
        exe.assert_not_called()
        apply_mock.assert_not_called()

    def test_one_pending_move_per_person(self):
        """AC-185-08 — a second concurrent request would carry a stale snapshot."""
        res, mk = _post(_client_hr(), TRANSFER, pending='req-existing')
        assert res.status_code == 409
        body = json.loads(res.data)
        assert body['pending_request_id'] == 'req-existing'
        mk.assert_not_called()


# ── 4. Company scoping (CLAUDE.md invariant 4) ────────────────────────────────

class TestCompanyScoping:
    def test_subject_in_another_company_is_refused(self, hr_client):
        with hr_client.session_transaction() as s:
            s['company_id'] = CO
        res, mk = _post(hr_client, TRANSFER,
                        subject={'company_id': OTHER_CO, 'employment_status': 'ACTIVE',
                                 'name': 'Other Tenant'})
        assert res.status_code == 403
        mk.assert_not_called()

    def test_foreign_business_unit_uuid_is_refused(self):
        """AC-185-16 — a valid UUID from another tenant, posted straight at the API."""
        res, mk = _post(_client_hr(), TRANSFER, unit_in_company=False)
        assert res.status_code == 403
        assert 'does not belong to this company' in json.loads(res.data)['error']
        mk.assert_not_called()

    def test_foreign_manager_is_refused(self):
        res, mk = _post(_client_hr(), TRANSFER,
                        manager={'company_id': OTHER_CO, 'employment_status': 'ACTIVE'})
        assert res.status_code == 403
        mk.assert_not_called()

    def test_request_is_created_against_the_subjects_company(self):
        """company_id comes from the affected employee, never from the session."""
        res, mk = _post(_client_hr(), TRANSFER)
        assert res.status_code == 200
        assert mk.call_args.args[0] == CO

    def test_prefill_refuses_another_companys_employee(self, hr_client):
        with hr_client.session_transaction() as s:
            s['company_id'] = CO
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query(
                 subject={'id': 'emp-x', 'company_id': OTHER_CO,
                          'employment_status': 'ACTIVE', 'name': 'Other',
                          'employee_number': 'E-9', 'job_title': 'Dev'})):
            res = hr_client.get('/api/org-change/prefill?subject=emp-x')
        assert res.status_code == 403

    def test_decide_refuses_another_companys_request(self):
        from app.services import org_change_service as svc
        req = {'id': 'req-1', 'company_id': OTHER_CO, 'employee_id': 'emp-sub',
               'requested_by_user_id': 'u-hr', 'current_step': 1, 'status': 'PENDING',
               'proposed_manager_id': 'm-new'}
        with patch.object(svc, 'query', side_effect=[req]), \
             patch.object(svc, 'execute') as exe:
            ok, msg = svc.decide('req-1', HR_USER, 'approve', None)
        assert ok is False and msg == 'not your company'
        exe.assert_not_called()

    def test_scoping_queries_never_widen_to_global_rows(self):
        """CLAUDE.md: `WHERE company_id = %s::uuid` only — never `OR company_id IS NULL`."""
        import inspect
        from app.routes import org_change as mod
        src = _norm(inspect.getsource(mod)).upper()
        assert 'COMPANY_ID IS NULL' not in src

    def test_employees_company_id_is_never_modified(self):
        """AC-185-19 — a cross-tenant move is a leave-and-rehire, not a transfer."""
        import inspect
        from app.services import org_change_service as svc
        src = _norm(inspect.getsource(svc)).upper()
        assert 'UPDATE EMPLOYEES' not in src


# ── 5. Same request, whichever entry point raised it (AC-185-06) ──────────────

class TestEntryPointsAreIndistinguishable:
    def test_identical_payloads_produce_identical_engine_calls(self):
        """Drag-and-drop and Transfer… differ only in how the form was filled."""
        payload = dict(TRANSFER)
        res_a, mk_a = _post(_client_hr(), payload)          # drag-and-drop
        res_b, mk_b = _post(_client_hr(), payload)          # Transfer…
        assert res_a.status_code == res_b.status_code == 200
        assert mk_a.call_args.args == mk_b.call_args.args

    def test_route_ignores_any_client_supplied_source_marker(self):
        """No branch on how the request was raised — there is only one path."""
        res, mk = _post(_client_hr(), dict(TRANSFER, source='transfer', mode='hr'))
        assert res.status_code == 200
        company_id, subject_id, user_id, proposed, reason = mk.call_args.args
        assert proposed == {'business_unit_id': 'bu-new', 'functional_unit_id': None,
                            'location_id': None, 'manager_id': 'm-new'}
        assert reason == 'Team realignment'
        assert user_id == 'u-hr'
        assert subject_id == 'emp-sub'
        assert company_id == CO

    def test_the_chain_is_the_companys_configured_chain(self):
        """The snapshot is taken from `workflow_steps` — one approval row per level."""
        from app.services import org_change_service as svc
        with patch.object(svc, 'current_placement', return_value=CURRENT_PLACEMENT), \
             patch.object(svc, 'workflow_steps', return_value=[STEP_1, STEP_2]) as ws, \
             patch.object(svc, 'query', return_value=None), \
             patch.object(svc, 'transaction', FakeTransaction()), \
             patch.object(svc, 'insert_returning', return_value={'id': 'req-1'}), \
             patch.object(svc, 'execute') as exe, \
             patch.object(svc, '_step_approver_user_ids', return_value=['u-hr']), \
             patch.object(svc, '_emp_name', return_value='Sub Ject'), \
             patch.object(svc, 'notif'):
            svc.create_request(CO, 'emp-sub', 'u-hr',
                               {'business_unit_id': 'bu-new', 'functional_unit_id': None,
                                'location_id': None, 'manager_id': 'm-new'}, 'Realignment')
        ws.assert_called_once_with(CO)
        approval_writes = [c for c in exe.call_args_list
                           if 'org_change_approvals' in _norm(c.args[0])]
        assert len(approval_writes) == 2
        assert [c.args[1][1] for c in approval_writes] == [1, 2]

    def test_unconfigured_company_still_gets_a_chain(self):
        """PD2 — the fallback is one HR_ADMIN level, never zero (never auto-apply)."""
        from app.services import org_change_service as svc
        with patch.object(svc, 'query', return_value=None):
            steps = svc.workflow_steps(CO)
        assert len(steps) == 1
        assert steps[0]['approver_role'] == 'HR_ADMIN'


# ── 6. Entry-point guards that keep bad requests out of the engine ────────────

class TestSubmissionGuards:
    def test_former_employee_cannot_be_transferred(self):
        """AC-185-12."""
        res, mk = _post(_client_hr(), TRANSFER,
                        subject={'company_id': CO, 'employment_status': 'TERMINATED',
                                 'name': 'Gone Away'})
        assert res.status_code == 400
        mk.assert_not_called()

    def test_inactive_manager_is_refused(self):
        res, mk = _post(_client_hr(), TRANSFER,
                        manager={'company_id': CO, 'employment_status': 'RESIGNED'})
        assert res.status_code == 400
        mk.assert_not_called()

    def test_self_manager_is_refused(self):
        res, mk = _post(_client_hr(), dict(TRANSFER, manager_id='emp-sub'))
        assert res.status_code == 400
        assert 'cannot report to themselves' in json.loads(res.data)['error']
        mk.assert_not_called()

    def test_reporting_cycle_is_refused(self):
        """AC-185-13 — the proposed manager already reports to the subject."""
        res, mk = _post(_client_hr(), TRANSFER, cycle=True)
        assert res.status_code == 400
        assert 'reporting loop' in json.loads(res.data)['error']
        mk.assert_not_called()

    def test_a_no_op_transfer_is_refused(self):
        """AC-185-11 — every proposed value equals the current placement."""
        res, mk = _post(_client_hr(), {'employee_id': 'emp-sub', 'manager_id': 'm-old',
                                       'business_unit_id': 'bu-cur', 'reason': 'none'})
        assert res.status_code == 400
        mk.assert_not_called()

    def test_an_empty_transfer_is_refused(self):
        res, mk = _post(_client_hr(), {'employee_id': 'emp-sub', 'reason': 'x'})
        assert res.status_code == 400
        mk.assert_not_called()

    def test_unknown_employee_is_refused(self):
        res, mk = _post(_client_hr(), TRANSFER, subject=None)
        assert res.status_code == 404
        mk.assert_not_called()

    def test_missing_employee_id_is_refused(self):
        res, mk = _post(_client_hr(), {'reason': 'x'})
        assert res.status_code == 400
        mk.assert_not_called()


# ── 7. Prefill — the dialog can never describe a chain the engine won't build ─

class TestPrefillContract:
    def _prefill(self, client, **stub):
        with patch('app.auth.can_access_feature', return_value=True), \
             patch('app.routes.org_change.query', side_effect=route_query(**stub)), \
             patch('app.routes.org_change.svc.current_placement', return_value=CURRENT_PLACEMENT), \
             patch('app.routes.org_change.svc.workflow_steps', return_value=[STEP_1, STEP_2]):
            res = client.get('/api/org-change/prefill?subject=emp-sub')
        return res, json.loads(res.data)

    def test_chain_labels_come_from_the_engines_own_config(self, hr_client):
        with hr_client.session_transaction() as s:
            s['company_id'] = CO
        res, body = self._prefill(hr_client)
        assert res.status_code == 200
        assert [c['label'] for c in body['approval_chain']] == ['HR Admin', 'Portal Admin']

    def test_direct_reports_are_reported_so_the_dialog_can_warn(self, hr_client):
        """AC-185-10 — the team does not move with the manager."""
        with hr_client.session_transaction() as s:
            s['company_id'] = CO
        res, body = self._prefill(hr_client, direct_reports=4)
        assert body['direct_reports'] == 4

    def test_pending_request_is_surfaced_before_the_form_is_shown(self, hr_client):
        with hr_client.session_transaction() as s:
            s['company_id'] = CO
        res, body = self._prefill(hr_client, pending='req-existing')
        assert body['pending_request_id'] == 'req-existing'

    def test_prefill_requires_write_access(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=False):
            res = hr_client.get('/api/org-change/prefill?subject=emp-sub')
        assert res.status_code in (302, 403)

    def test_creation_requires_write_access(self, hr_client):
        with patch('app.auth.can_access_feature', return_value=False):
            res = hr_client.post('/api/org-change/request',
                                 data=json.dumps(TRANSFER), content_type='application/json')
        assert res.status_code in (302, 403)

    def test_creation_requires_login(self, client):
        res = client.post('/api/org-change/request',
                          data=json.dumps(TRANSFER), content_type='application/json')
        assert res.status_code == 302
