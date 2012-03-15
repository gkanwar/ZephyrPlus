// When the document loads, populate the personals
$(document).ready(function()
{
    $("#personals_sidebar").resizable({handles:'s',minHeight: 20});
    $("#personals_anchor").css({height:$("#personals_sidebar").height()-20});
    $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20});
				 
    $("#personals_sidebar").resize(function()
				  {
				      $("#personals_anchor").css({height:$("#personals_sidebar").height()-20});
				      $("#classes_sidebar").css({height:$("#dropdown").height()-$("#personals_sidebar").height()});
				      $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20});
				  });    

    $("#messages").lionbars();
    $("#personals_anchor").lionbars();
    $("#classes_anchor").lionbars();

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
    console.log(maxPersonals);
    for (var i = 0; i < personals.length; i++)
    {
	ul.append("<li>" + personals[i] + "</li>");
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
    for (var i = 0; i < classes.length; i++)
    {
	if (i == maxClasses)
	{
	    break;
	}
	ul.append("<li class='classes_entry'><img src='img/dropdown-inactive.png' onclick='$(this).parent().children(\".dropdown\").slideToggle(); $(this).attr(\"src\", $(this).attr(\"src\") == \"img/dropdown-active.png\" ? \"img/dropdown-inactive.png\" : \"img/dropdown-active.png\")'/>"+ 
		  "<span onclick='fillMessages(\""+classes[i]+"\")'>" + classes[i] + "</span>" +
		  "<ul class='dropdown' style='display:none'>\
                       <li onclick='fillMessages(\""+classes[i]+"\", \"Subclass 1\")'>Subclass-1</li>\
                       <li onclick='fillMessages(\""+classes[i]+"\", \"Subclass 2\")'>Subclass-2</li>\
                   </ul></li>");
    }
    root.html(ul);
};

var fillMessages = function(klass, instance)
{
    var headerText = "all classes";
    // Class is defined
    if (klass)
    {
	headerText += " >  " + klass;
    }
    // Instance is defined
    if (instance)
    {
	headerText += " > " + instance;
    }

    $("#chatheader").text(headerText);
};

