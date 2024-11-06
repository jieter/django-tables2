.. _builtin-columns:

Built-in columns
================

For common use-cases the following columns are included:

- `.BooleanColumn` -- renders boolean values
- `.CheckBoxColumn` -- renders ``checkbox`` form inputs
- `.Column` -- generic column
- `.DateColumn` -- date formatting
- `.DateTimeColumn` -- ``datetime`` formatting in the local timezone
- `.EmailColumn` -- renders ``<a href="mailto:...">`` tags
- `.FileColumn` -- renders files as links
- `.JSONColumn` -- renders JSON as an indented string in ``<pre></pre>``
- `.LinkColumn` -- renders ``<a href="...">`` tags (compose a Django URL)
- `.ManyToManyColumn` -- renders a list objects from a `ManyToManyField`
- `.TemplateColumn` -- renders template code
- `.TimeColumn` -- time formatting
- `.URLColumn` -- renders ``<a href="...">`` tags (absolute URL)
