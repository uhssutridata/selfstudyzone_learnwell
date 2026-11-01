# Learnwell LMS

A Django learning management system starter for self-paced courses. Learners can discover and search published courses, create an account, enroll, read lessons, mark lessons complete, and track progress. Staff manage courses and lessons through Django Admin.

## Run locally

```bash
cd lms
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000. Admin is at `/admin/`. Add a course, set a unique slug, add lessons inline, and check **Published** to make it visible in Explore. Learner signup is at `/signup/`.

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

For deployment, set `DJANGO_SECRET_KEY` to a secure random value, set `DJANGO_DEBUG=0`, and provide production hosts in `DJANGO_ALLOWED_HOSTS`. SQLite is configured for local development; production deployments should use managed database settings and a production web server.
