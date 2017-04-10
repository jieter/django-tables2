.. _builtin-columns:

Built-in columns
================

For common use-cases the following columns are included:

- `.BooleanColumn` -- renders boolean values
- `.Column` -- generic column
- `.CheckBoxColumn` -- renders checkbox form inputs
- `.DateColumn` -- date formatting
- `.DateTimeColumn` -- datetime formatting in the local timezone
- `.EmailColumn` -- renders ``<a href="mailto:...">`` tags
- `.FileColumn` -- renders files as links
- `.JSONColumn` -- renders JSON as an indented string in ``<pre></pre>``
- `.LinkColumn` -- renders ``<a href="...">`` tags (compose a django url)
- `.RelatedLinkColumn` -- renders ``<a href="...">`` tags linking related objects
- `.TemplateColumn` -- renders template code
- `.URLColumn` -- renders ``<a href="...">`` tags (absolute url)
