Performance
-----------

Django-tables tries to be efficient in displaying big datasets. It tries to
avoid converting the `~django.db.models.query.QuerySet` instances to lists by
using SQL to slice the data and should be able to handle datasets with 100k
records without a problem.

However, when using one of the customisation methods described in this
documentation, there is lot's of oppurtunity to introduce slowness.
If you experience that, try to strip the table of customisations and re-add them
one by one, checking for performance after each step.
