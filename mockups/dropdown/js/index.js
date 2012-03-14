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

        $('#messages').lionbars();

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

    var root = $("#classes_anchor");
    var ul = $("<ul></ul>");
    for (var i = 0; i < classes.length; i++)
    {
	if (i == maxClasses)
	{
	    break;
	}
	var class_entry = $("<li class='classes_entry'><img src='img/dropdown-inactive.png' onclick='$(this).parent().children(\".dropdown\").slideToggle(); $(this).attr(\"src\", $(this).attr(\"src\") == \"img/dropdown-active.png\" ? \"img/dropdown-inactive.png\" : \"img/dropdown-active.png\")'/>" + 
		  "<span onclick='fillMessages(\""+classes[i].id+"\")'>" + classes[i].name + "</span>" +
	          "</li>");
	ul.append(class_entry);

	var instances_ul = $("<ul class='dropdown' style='display:none'/>");
	class_entry.append(instances_ul);

	for (var j = 0; j < classes[i].instances.length; j++)
	{
	    instances_ul.append("<li onclick='fillMessages(\""+classes[i].id+"\", \""+instances[j].id+"\")'>"+instances[j].name+"</li>");
	}
    }
    root.html(ul);
};

var fillMessages = function(class_id, instance_id)
{
    var headerText = "all classes";
    var messages;
    // Class is defined
    if (class_id)
    {
	headerText += " >  " + classes[class_id].name;
	// Instance is defined
	if (instance_id)
	{
	    headerText += " > " + instances[instance_id].name;
	    messages = instances[instance_id].messages;
	}
	else
	{
	    messages = classes[class_id].messages;
	}

	// Actually fill in the messages
	$("#messages").html('');
	for (var i in messages)
	{
	    var message_entry = $("<div class='message_entry'/>");
	    var header = $("<div class='message_header'/>").text(messages[i].sender); // For now
	    var body = $("<div class='message_body'/>").text(messages[i].message);
	    message_entry.append(header).append(body);
	    $("#messages").append(message_entry);
	}

    }

    $("#chatheader").text(headerText);
};

