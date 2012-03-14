// When the document loads, populate the personals
$(document).ready(function()
{
    $("#personals_sidebar").resizable({handles:'s',minHeight: 20});
    $("#personals_anchor").css({height:$("#personals_sidebar").height()-20}); 
    $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20})
				 
    $("#personals_sidebar").resize(function()
				  {
				      $("#personals_anchor").css({height:$("#personals_sidebar").height()-20});
				      $("#classes_sidebar").css({height:$("#dropdown").height()-$("#personals_sidebar").height()});
				      $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20});
				  });    

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
    root = $("#classes_anchor");
    ul = $("<ul></ul>");
    console.log("loading classes");
    console.log(classes);
    for (var i = 0; i < classes.length; i++)
    {
	ul.append("<li>" + classes[i] + "</li>");
    }
    root.html(ul);
};
