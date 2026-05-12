# 🧪 Online Testing System (Django)

A Django-based platform for managing and conducting online tests. Candidates register, take tests, view results and history, manage membership plans, and can delete their account. Admins use Django Admin to see all users, delete accounts, and assign membership plans.

---

## 🚀 Features

- 🧑‍💼 Admin panel for managing questions, tests, users, and membership plans
- 👥 User registration and login
- 📝 Multiple-choice questions with auto-scoring
- 📊 Result calculation and display
- 📱 Responsive design (Tailwind CSS)
- 🎫 Membership plans with test-type access control
- 🗑️ User account deletion

---

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SURYASSACHINP22/ONline_testing_app_django.git
   cd ONline_testing_app_django
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create local environment file**
   ```bash
   copy .env.example .env
   ```
   Update `.env` values as needed (keep `DJANGO_DEBUG=True` for local development).

5. **Run migrations and create admin user**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser   # For admin access
   ```

6. **Run the server**
   ```bash
   python manage.py runserver
   ```

7. Open:
   - **http://127.0.0.1:8000/** (redirects to OTS)
   - **http://127.0.0.1:8000/admin/** (admin panel)
   - **http://127.0.0.1:8000/api/schema/swagger-ui/** (API docs)

---

## 📌 Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, Tailwind CSS
- **Database:** SQLite

---

## 📐 Design Patterns

See **[DESIGN_PATTERNS.md](DESIGN_PATTERNS.md)** for MVT, LLD patterns (decorator, service layer), and system design.

**Admin login:** See **[ADMIN_LOGIN.md](ADMIN_LOGIN.md)** — create superuser, then open `/admin/`.

---

## 🤝 Contributing

1. Fork the repo
2. Create your branch: `git checkout -b feature/feature-name`
3. Commit your changes: `git commit -m "Add feature"`
4. Push the branch: `git push origin feature/feature-name`
5. Open a pull request

---

## 📄 License

This project is open-source and available under the MIT License.

## 📧 Contact

GitHub: [@SURYASSACHINP22](https://github.com/SURYASSACHINP22)
