from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0010_homepagesettings_lesson_label_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="homepagesettings",
            name="all_topics_label",
        ),
    ]
