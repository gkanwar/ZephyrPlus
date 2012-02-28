// When the document loads, populate the personals
$(document).ready(function()
{
    loadPersonals();
    loadClasses();
});

// Constant defining max number of personals to display in the sidebar
var maxPersonals = 5;

// Load the personals to display in the sidebar
var loadPersonals = function()
{
    root = $("#personals_anchor");
    ul = $("<ul></ul>");
    console.log("loading personals");
    console.log(personals);
    for (var i = 0; i < personals.length; i++)
    {
	if (i == maxPersonals)
	{
	    break;
	}
	ul.append("<li>" + personals[i] + "</li>");
    }
    if (personals.length > maxPersonals)
    {
	ul.append("<li>...</li>");
    }
    root.html(ul);
};

// Constant defining max number of classes to display in the sidebar
var maxClasses = 5;

// Load the classes to display in the sidebar
var loadClasses = function()
{
    root = $("#classes_anchor");
    ul = $("<ul></ul>");
    console.log("loading classes");
    console.log(classes);
    for (var i = 0; i < classes.length; i++)
    {
	if (i == maxClasses)
	{
	    break;
	}
	ul.append("<li>" + classes[i] + "</li>");
    }
    if (personals.length > maxPersonals)
    {
	ul.append("<li>...</li>");
    }
    root.html(ul);
};