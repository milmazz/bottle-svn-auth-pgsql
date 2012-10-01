<!DOCTYPE html>
<html lang="en">
<head>
	{% block htmlhead %}
	<meta charser="utf-8">
	<title>{% block title %}{% endblock %}</title>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">

	 <!-- Le styles -->
	<link href="/bootstrap/css/bootstrap.min.css" rel="stylesheet">
	<link href="/bootstrap/css/bootstrap-responsive.css" rel="stylesheet">

	<!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="//html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
	{% endblock %}
</head>
<body>
	<div id="content">
		{% block content %}{% endblock %}
	</div>
	<script src="http://code.jquery.com/jquery-latest.js"></script>
	<script src="/bootstrap/js/bootstrap.min.js"></script>
</body>
</html>
