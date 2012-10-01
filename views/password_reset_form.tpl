{% extends "base.tpl" %}
{% block title %}Password reset{% endblock %}

{% block content %}
<div class="hero-unit">
	<h1>Password reset</h1>

	<p>Forgotten your password? Enter your username below, and
	we'll e-mail instructions for setting new one</p> 

	<form method="POST" action="/password_reset" class="form-horizontal">
        {% if form.username.errors or invalid %}
	<div class="alert alert-error">
	<ul>{% for error in form.username.errors %}
		<li>{{ error }}</li>
	{% endfor %}
	{% if invalid %}
	<li>Username didn't exists.</li>
	{% endif %}
	</ul>
	</div>
	{% endif %}

	<div class="input-prepend">
      	<span class="add-on"><i class="icon-user"></i></span>
      	<input id="username" name="username" type="text" placeholder="Username" autofocus>
    	</div>

	{{ form.submit(class="btn btn-primary") }}
	</form>
</div>
{% endblock %}
