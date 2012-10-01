{% extends "base.tpl" %}
{% block title %}Password reset{% endblock %}

{% block content %}
<div class="hero-unit">
{% if error %}
<h1>Password reset unsuccessful</h1>
<p>The password reset link was invalid, possibly because it has already been used.  Please request a new password reset.</p>
{% else %}
<h1>Password reset confirm</h1>
<p>Please enter your new password twice so we can verify you typed it in correctly.</p>
<form method="POST" action="/reset" class="form-inline">
<div class="alert alert-error">
{% if form.new_pass.errors %} <ul>{% for error in form.new_pass.errors %}<li>{{ error }}</li>{% endfor %}</ul>{% endif %}
</div>
{{ form.username }}
{{ form.new_pass.label }} {{ form.new_pass }}
{{ form.confirm_pass.label }} {{ form.confirm_pass }} {% if form.confirm_pass.errors %} <ul>{% for error in form.confirm_pass.errors %}<li>{{ error }}</li>{% endfor %}</ul>{% endif %}

{{ form.submit(class="btn btn-primary") }}</p>
</form>
{% endif %}
</div>
{% endblock %}
