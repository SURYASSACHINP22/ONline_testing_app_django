# Design Patterns Used in This Application

## 1. **MVT (Model–View–Template)**

Django’s built-in pattern:

- **Models** (`OTS/models.py`): Data layer — `Candidate`, `Question`, `Result`, `MembershipPlan`. Define structure and behavior of data.
- **Views** (`OTS/myview.py`): Request handlers. Process HTTP requests, use models, and pass context to templates.
- **Templates** (`OTS/templates/`): Presentation. HTML with Django template language; no business logic.

So the app is structured as **MVT**: models for data, views for logic, templates for UI.

---

## 2. **Django Admin (RBAC for staff)**

- **Who:** Only staff/superuser accounts (Django’s auth) can access `/admin/`.
- **What:** Admin can:
  - See all user accounts (Candidates), delete them, and assign/change membership plans.
  - Manage membership plans (create, edit, activate/deactivate).
  - View and manage questions and results (read-only or full, as configured).
- **Pattern:** Role-based access: normal users use OTS app; admins use Django admin with elevated permissions.

**Create an admin user (one-time):**

```bash
python manage.py createsuperuser
```

Then open **http://127.0.0.1:8000/admin/** and log in with that user. See **ADMIN_LOGIN.md** for step-by-step instructions.

---

## 3. **Access control by membership (test types)**

- **Membership plan** controls **which test types** a user can take (e.g. 1-, 3-, or 5-question tests).
- **Policy:** Before starting a test, the view checks: "Is this user's plan allowed to take a test of N questions?"
- **Implementation:** `MembershipPlan.allowed_question_counts` (e.g. `"1,3,5"`). Helper `_allowed_question_counts_for_candidate(candidate)` returns the list of allowed sizes. `testPaper` view denies access if `n` is not in that list and redirects with a message.
- **No plan:** User is treated as "allow all" (1, 3, 5).

---

## 4. **Session-based authentication**

- **Pattern:** Session (cookie + server-side session store) identifies the logged-in candidate.
- **Flow:** Login sets `request.session['username']` and `request.session['name']`; protected views check these and redirect to login if missing; logout clears them.
- **Separation:** App users are **Candidates** (OTS); admin users are **Django User** (auth). Two separate “user” concepts: candidates for the app, staff/superuser for admin.

---

## 5. **Flash messages**

- One-time messages (e.g. “Account deleted”, “Membership updated”) are stored in `request.session['flash_message']`, then shown in the next template and removed (e.g. `pop`) so they don’t repeat.
- Pattern: **Post–Redirect–Get** with a short-lived session key for user feedback.

---

## 6. **Optional future patterns**

- **Service layer:** Move business logic (e.g. “submit test”, “delete account”, “assign plan”) from views into service functions or a small `OTS/services.py` module. Views would call services and only handle HTTP in/out. Keeps views thin and logic testable.
- **Repository:** Wrap model access in a small repository layer if you want to abstract the ORM (e.g. for testing or swapping storage later). Not required for the current size of the app.

---

**Summary:** The app uses **MVT** for structure, **Django Admin** for admin-only actions (see/delete users, assign membership), **session-based auth** for candidates, and **flash messages** for one-time feedback. No separate “admin candidate” in OTS — admin is done via Django’s built-in admin and `createsuperuser`.

## LLD (Low-Level Design) Patterns

**Currently used:** MVT, Policy/Strategy (allowed test types), Post-Redirect-Get, Session as state.

**Implemented:** **Decorator** (`OTS/decorators.py`: `@candidate_login_required` on all candidate-only views), **Service layer** (`OTS/services.py`: `get_allowed_question_counts`, `calculate_and_save_result`, `delete_candidate_account`, `assign_membership_plan`, `authenticate_candidate`, `register_candidate`, `evaluate_answer`). Views are thin; logic is testable in services.

**System design:** Structure = **MVT**; Access = **policy check**; Admin = **Django Admin (RBAC)**; Auth = **session**; Feedback = **flash messages**. Root URL (`/`) redirects to `/OTS/` as the default landing page.
