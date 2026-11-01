# Learnwell LMS

A Django learning management system starter for self-paced courses. Learners can discover and search published courses, create an account, enroll, read lessons, mark lessons complete, and track progress. Staff manage courses and lessons through Django Admin.

## Run with Docker Compose and PostgreSQL

Docker Compose starts PostgreSQL, the Django application, and Nginx. PostgreSQL data and uploaded media are kept in named volumes so recreating containers does not erase them.

The PostgreSQL database starts empty; records in an existing local `db.sqlite3` file are not copied automatically.

1. Copy `.env.example` to `.env` and replace `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD` with strong, private values.
2. Start the app:

   ```bash
   docker compose up --build -d
   ```

3. Open http://localhost:8000. Create an administrator account with:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

View logs with `docker compose logs -f`. Stop the app with `docker compose down`; its database and media volumes remain. `docker compose down -v` also deletes those volumes and their data.

For a VPS, set `DJANGO_ALLOWED_HOSTS` to the domain/IP and `DJANGO_CSRF_TRUSTED_ORIGINS` to its full origin, such as `https://learn.example.com`. Put TLS in front of this Compose stack with a reverse proxy or a TLS-enabled web server before exposing it publicly.

## Run locally without Docker

```bash
cd lms
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The non-Docker setup also uses PostgreSQL. Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, and `DB_PORT` in your environment and make sure that PostgreSQL is running before applying migrations. Open http://127.0.0.1:8000. Admin is at `/admin/`. A superuser creates and manages courses, selecting the target class and subject for each course. Lessons inherit that class and subject. Add lessons inline on a course; then open **Lessons** in admin to add multiple-choice questions. Lessons can include text, a YouTube video, an animated SVG, and homework instructions. Students take the quiz and upload homework on the lesson page. Check **Published** to make a course visible to eligible students in Explore. Learner signup is at `/signup/`.

To add the editable sample course with animated SVG, Manim/3Blue1Brown video lessons, quizzes, and homework, first create or retain a teacher account, then run:

```bash
python manage.py load_sample_lessons
```

The sample course is published and can be edited under **Courses**, **Lessons**, and **Lesson quiz attempts** in Django admin.

## Parent and teacher student records

After parent signup, the parent is sent to Parent space to search students whose registered father or mother name matches the parent name. Access requests appear under **Admin → Parent watchlists** and must be approved before performance details are shown. A teacher must be verified under **Admin → Teacher details** before reviewing homework. Teachers can review work from students they registered or students an administrator assigned under **Admin → Teacher student approvals**. Teachers do not create courses; superusers manage courses and lesson content.

Students upload lesson homework on the lesson page. Verified teachers can open their student directory, download submissions, and leave feedback. Student sessions report active, visible LMS time while a student is signed in. Parents with an approved watchlist link can see exam results, homework status, and recorded time in their dashboard.

Students start on the free subscription. They can request a paid upgrade from their dashboard; an administrator confirms payment and activates the paid plan from **Admin → Subscriptions**. No payment gateway or price is configured in this starter.

## Git history

This project has its own Git repository in this folder. Save later versions with:

```bash
git add .
git commit -m "Describe your changes"
git log --oneline
git revert <commit>
```

`git revert` creates a new commit that undoes a selected commit while preserving history. To inspect an older version without changing your current files, use `git switch --detach <commit>`.

## Configuration

The application is configured for PostgreSQL (not SQLite). Docker Compose supplies the database connection settings, and production deployments should set a private `DJANGO_SECRET_KEY`, use `DJANGO_DEBUG=0`, and provide the correct `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` values.
