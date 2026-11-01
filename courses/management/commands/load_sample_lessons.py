from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.models import Course, Lesson, LessonQuestion, UserProfile


TANGENT_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 380" role="img" aria-labelledby="title desc">
  <title id="title">A radius meets a tangent at a right angle</title>
  <desc id="desc">A fixed circle with radius OT meeting a tangent at T, with a pulsing right angle marker.</desc>
  <defs>
    <linearGradient id="bg" x2="1" y2="1"><stop stop-color="#f4f7ed"/><stop offset="1" stop-color="#fff"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="4" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="720" height="380" rx="24" fill="url(#bg)"/>
  <circle cx="265" cy="190" r="112" fill="#e6eddc" stroke="#456c3a" stroke-width="5"/>
  <line x1="265" y1="190" x2="377" y2="190" stroke="#b47740" stroke-width="6" stroke-linecap="round"/>
  <line x1="377" y1="48" x2="377" y2="332" stroke="#486d9b" stroke-width="6" stroke-linecap="round"/>
  <path d="M377 190h-28v-28" fill="none" stroke="#df7b48" stroke-width="5" stroke-linejoin="round" filter="url(#glow)">
    <animate attributeName="opacity" values=".35;1;.35" dur="2s" repeatCount="indefinite"/>
  </path>
  <circle cx="265" cy="190" r="7" fill="#293b28"/><circle cx="377" cy="190" r="8" fill="#df7b48"/>
  <text x="246" y="220" fill="#293b28" font-family="system-ui,sans-serif" font-size="24" font-weight="700">O</text>
  <text x="390" y="197" fill="#293b28" font-family="system-ui,sans-serif" font-size="24" font-weight="700">T</text>
  <text x="305" y="174" fill="#80552f" font-family="system-ui,sans-serif" font-size="18" font-weight="700">radius</text>
  <text x="400" y="83" fill="#3f6089" font-family="system-ui,sans-serif" font-size="18" font-weight="700">tangent</text>
  <text x="470" y="180" fill="#293b28" font-family="Georgia,serif" font-size="35" font-weight="700">OT ⟂ tangent</text>
  <text x="470" y="222" fill="#456c3a" font-family="Georgia,serif" font-size="31">∠OTangent = 90°</text>
  <text x="470" y="273" fill="#737a6d" font-family="system-ui,sans-serif" font-size="15">The circle stays still;</text>
  <text x="470" y="296" fill="#737a6d" font-family="system-ui,sans-serif" font-size="15">the right angle is highlighted.</text>
</svg>'''

PARABOLA_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 380" role="img" aria-labelledby="title desc">
  <title id="title">A moving point traces a parabola</title>
  <desc id="desc">An animated point travels along the graph y equals x squared.</desc>
  <defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#f2f5ec"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>
  <rect width="720" height="380" rx="24" fill="url(#bg)"/>
  <line x1="105" y1="300" x2="455" y2="300" stroke="#88917f" stroke-width="3"/><line x1="280" y1="330" x2="280" y2="55" stroke="#88917f" stroke-width="3"/>
  <path d="M145 300 Q280 90 415 300" fill="none" stroke="#547c43" stroke-width="6"/>
  <circle r="9" fill="#df8047"><animateMotion dur="4s" repeatCount="indefinite" path="M145 300 Q280 90 415 300"/></circle>
  <text x="485" y="150" fill="#293b28" font-family="Georgia,serif" font-size="34" font-weight="700">y = x²</text>
  <text x="485" y="194" fill="#626c5b" font-family="system-ui,sans-serif" font-size="17">Each x-value gives</text>
  <text x="485" y="219" fill="#626c5b" font-family="system-ui,sans-serif" font-size="17">a point on the curve.</text>
  <text x="455" y="307" fill="#626c5b" font-family="system-ui,sans-serif" font-size="15">x</text><text x="290" y="65" fill="#626c5b" font-family="system-ui,sans-serif" font-size="15">y</text>
</svg>'''


LESSONS = [
    {
        "title": "Why a tangent meets the radius at 90°",
        "content_type": Lesson.ContentType.ANIMATED,
        "content": "A tangent touches a circle at exactly one point. Draw the radius from the centre O to that point T: it is perpendicular to the tangent. The animated diagram highlights the right angle without rotating the circle.",
        "youtube_url": "",
        "homework_description": "Draw a circle with centre O and a tangent touching it at T. Add the radius OT, mark the right angle, and explain why the tangent is perpendicular to OT. Upload a photo or a PDF of your work.",
        "duration_minutes": 12,
        "questions": [
            ("At the point where a tangent touches a circle, what is the angle between the tangent and the radius?", "45°", "60°", "90°", "180°", "c", "The radius to the point of tangency is perpendicular to the tangent."),
            ("How many points does a tangent line share with a circle?", "Zero", "Exactly one", "Exactly two", "Infinitely many", "b", "A tangent touches the circle at exactly one point."),
        ],
        "animation": True,
    },
    {
        "title": "From a circle to the area formula",
        "content_type": Lesson.ContentType.VIDEO,
        "content": "Watch a visual derivation connecting the geometry of a circle to calculus. As you watch, notice how thin circular rings can be rearranged into a shape whose area is easier to calculate. Video by 3Blue1Brown.",
        "youtube_url": "https://www.youtube.com/watch?v=WUvTyaaNkzM",
        "homework_description": "In your own words, describe how slicing a circle into thin rings helps explain its area. Include a labelled sketch and upload your work.",
        "duration_minutes": 18,
        "questions": [
            ("Which expression gives the area of a circle with radius r?", "2πr", "πr²", "πd", "r²/π", "b", "The area is π multiplied by the square of the radius."),
            ("In the visual slicing idea, the small pieces are arranged to resemble which shape?", "A rectangle or parallelogram", "A pentagon", "A sphere", "A cone", "a", "The rings can be unwrapped into a shape with height r and base πr."),
        ],
        "animation": False,
    },
    {
        "title": "How Manim turns equations into animation",
        "content_type": Lesson.ContentType.VIDEO,
        "content": "This introductory Manim Community tutorial demonstrates how Python code can build and animate mathematical objects. Watch for the way a scene is assembled from shapes, labels, and timed transformations. Video by Theorem of Beethoven.",
        "youtube_url": "https://www.youtube.com/watch?v=rUsUrbWb2D4",
        "homework_description": "Plan a short 3-scene Manim animation for one school concept. List the objects, labels, and transformations you would show. Upload your storyboard or Python file.",
        "duration_minutes": 20,
        "questions": [
            ("What is Manim mainly used to create?", "Database tables", "Mathematical animations", "Music playlists", "Web forms", "b", "Manim is an animation engine for explanatory math videos."),
            ("In a Manim scene, what does a transformation do?", "Changes or moves visual objects", "Sends an email", "Creates a database", "Changes a password", "a", "Transformations animate changes to mathematical objects in a scene."),
        ],
        "animation": False,
    },
    {
        "title": "A Manim demo: planning a mathematical scene",
        "content_type": Lesson.ContentType.VIDEO,
        "content": "Watch Ben Sparks and 3Blue1Brown discuss and demonstrate the process behind animated mathematical explanations. Use the example to think about how a visual idea can be broken into understandable steps.",
        "youtube_url": "https://www.youtube.com/watch?v=rbu7Zu5X1zI",
        "homework_description": "Choose a concept from algebra, geometry, or physics. Write a short narration and sketch three frames that would make the idea easier to see.",
        "duration_minutes": 15,
        "questions": [
            ("What should a clear educational animation do?", "Decorate every frame", "Reveal an idea in understandable steps", "Avoid labels", "Move every object at once", "b", "Good explanatory animation guides attention through the idea one step at a time."),
            ("What is a useful first step when planning a math animation?", "Choose the key idea and visual objects", "Add random effects", "Write the credits first", "Hide the equation", "a", "Start with the concept and decide which objects make it visible."),
        ],
        "animation": False,
    },
    {
        "title": "Read a graph: the parabola y = x²",
        "content_type": Lesson.ContentType.TEXT,
        "content": "A graph shows how an output changes when an input changes. For y = x², choose an x-value, square it, then plot (x, y). The curve is symmetric because x and −x have the same square. Try following several points from left to right.",
        "youtube_url": "",
        "homework_description": "Complete a value table for x = −3, −2, −1, 0, 1, 2, 3. Plot each (x, y) pair and describe the symmetry you notice. Upload your graph.",
        "duration_minutes": 10,
        "questions": [
            ("What is y when x = −3 for y = x²?", "−9", "−6", "6", "9", "d", "Squaring −3 gives (−3) × (−3) = 9."),
            ("Why is the graph of y = x² symmetric about the y-axis?", "Because x² = (−x)²", "Because x² is always negative", "Because y equals x", "Because it has no vertex", "a", "Opposite x-values produce the same y-value."),
        ],
        "animation": False,
    },
    {
        "title": "Watch a point trace the parabola",
        "content_type": Lesson.ContentType.ANIMATED,
        "content": "Follow the moving point as it traces y = x². Its horizontal position is x and its vertical position is the square of x. Compare the left and right sides of the curve.",
        "youtube_url": "",
        "homework_description": "Sketch y = x² and mark the points for x = −2, −1, 0, 1, 2. Label the vertex and upload your sketch.",
        "duration_minutes": 8,
        "questions": [
            ("What are the coordinates of the vertex of y = x²?", "(0, 0)", "(1, 1)", "(0, 1)", "(−1, 0)", "a", "The smallest value of x² is 0, which occurs at x = 0."),
            ("What happens to y = x² when x changes from 2 to −2?", "It becomes negative", "It stays 4", "It becomes 2", "It becomes 0", "b", "Both 2² and (−2)² equal 4."),
        ],
        "animation": "parabola",
    },
]


class Command(BaseCommand):
    help = "Create an editable sample visual-mathematics course with lessons, quizzes and homework."

    @transaction.atomic
    def handle(self, *args, **options):
        teacher_profile = UserProfile.objects.filter(role=UserProfile.Role.TEACHER).select_related("user").order_by("user__username").first()
        if not teacher_profile:
            raise CommandError("Create a teacher account first, then run this command again.")

        course, _ = Course.objects.update_or_create(
            slug="sample-visual-mathematics",
            defaults={
                "title": "Visual Mathematics: Circles, Calculus & Manim",
                "subtitle": "Explore geometry through animations, videos and short quizzes.",
                "description": "An editable sample course demonstrating text lessons, animated SVG, embedded Manim and 3Blue1Brown videos, multiple-choice quizzes, and homework reviewed by authorized teachers.",
                "instructor": teacher_profile.user,
                "category": "Mathematics",
                "class_name": "8",
                "subject": "mathematics",
                "level": "Beginner",
                "published": True,
            },
        )

        for position, lesson_data in enumerate(LESSONS, start=1):
            lesson, _ = Lesson.objects.update_or_create(
                course=course,
                position=position,
                defaults={key: value for key, value in lesson_data.items() if key not in {"questions", "animation"}},
            )
            if lesson_data["animation"] and not lesson.animation_file:
                svg_data, filename = (PARABOLA_SVG, "parabola-tracing.svg") if lesson_data["animation"] == "parabola" else (TANGENT_SVG, "circle-tangent-right-angle.svg")
                lesson.animation_file.save(filename, ContentFile(svg_data.encode("utf-8")), save=True)
            for question_position, item in enumerate(lesson_data["questions"], start=1):
                prompt, option_a, option_b, option_c, option_d, correct_option, explanation = item
                LessonQuestion.objects.update_or_create(
                    lesson=lesson,
                    position=question_position,
                    defaults={
                        "prompt": prompt,
                        "option_a": option_a,
                        "option_b": option_b,
                        "option_c": option_c,
                        "option_d": option_d,
                        "correct_option": correct_option,
                        "explanation": explanation,
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(LESSONS)} sample lessons into '{course.title}'. Edit them in Django admin under Courses, Lessons, and Lesson questions."))
