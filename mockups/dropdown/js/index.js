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
    // TODO: Make an AJAX call to get the personals data

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
	ul.append("<li class='personals_entry'>" + personals[i] + "</li>");
    }
    if (personals.length > maxPersonals)
    {
	ul.append("<li class='personals_entry'>...</li>");
    }
    root.html(ul);
};

// Constant defining max number of classes to display in the sidebar
var maxClasses = 5;

// Load the classes to display in the sidebar
var loadClasses = function()
{
    // TODO: Load the classes via AJAX

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
	ul.append("<li class='classes_entry'><img src='img/dropdown-inactive.png' onclick='$(this).parent().children(\".dropdown\").slideToggle(); $(this).attr(\"src\", $(this).attr(\"src\") == \"img/dropdown-active.png\" ? \"img/dropdown-inactive.png\" : \"img/dropdown-active.png\")'/>"+ 
		  classes[i] + "<ul class='dropdown' style='display:none'>\
                                    <li>Subclass-1</li>\
                                    <li>Subclass-2</li>\
                                </ul></li>");
    }
    if (classes.length > maxClasses)
    {
	ul.append("<li>...</li>");
    }
    root.html(ul);
};