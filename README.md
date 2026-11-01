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

## Parent and teacher student records

After parent signup, the parent is sent to Parent space to search students whose registered father or mother name matches the parent name. Access requests appear under **Admin → Parent watchlists** and must be approved before performance details are shown. Teachers can search student records after an administrator verifies the teacher profile under **Admin → Teacher details**. School teachers are limited to students at their registered school; verified private tutors can search across schools.

Verified teachers can record exam marks/pass status and homework completion from a student record. Student sessions report active, visible LMS time while a student is signed in. Parents with an approved watchlist link can see exam results, homework status, and recorded time in their dashboard.

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

For deployment, set `DJANGO_SECRET_KEY` to a secure random value, set `DJANGO_DEBUG=0`, and provide production hosts in `DJANGO_ALLOWED_HOSTS`. SQLite is configured for local development; production deployments should use managed database settings and a production web server.
