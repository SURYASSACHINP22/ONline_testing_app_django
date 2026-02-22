# How to log in to Admin

The **admin** is separate from normal user (candidate) login. Only a **Django superuser** can access the admin site.

## 1. Create an admin user (one-time)

In the project folder, run:

```bash
python manage.py createsuperuser
```

You will be asked for:

- **Username** (e.g. `admin`)
- **Email** (can be blank; press Enter to skip)
- **Password** (twice; must match)

## 2. Log in to admin

1. Start the server: `python manage.py runserver`
2. Open in browser: **http://127.0.0.1:8000/admin/**
3. Log in with the **superuser username and password** (not your OTS candidate account).

## 3. What you can do in Admin

- **Candidates:** See all user accounts, delete users, assign or change **Membership plan**.
- **Membership plans:** Create/edit plans. Set **Allowed question counts** (e.g. `1,3,5`) to control which test types (1-, 3-, or 5-question tests) that plan allows.
- **Results / Questions:** View and manage as needed.

Admin is the only place that can delete any user and assign membership plans; normal users can only delete their own account and choose a plan from the Membership plans page.
