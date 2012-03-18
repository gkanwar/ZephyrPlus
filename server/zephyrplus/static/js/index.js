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

    $("#classes_title").click(function()
			      {
				  fillMessagesByClass();
			      });
    $("#personals_title").click(function()
				{
				    fillMessagesByPersonal();
				});

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

	// Call everything in its own function to make it scope right
	(function()
	 {
	     var curClass = classes[i];
	     var class_entry = $("<li/>");
	     var class_entry_div = $("<div/>")
		 .addClass("classes_entry")
		 .click(function()
			{
			    fillMessagesByClass(curClass.id);
			});
	     var dropdown_triangle = $("<img src='img/dropdown-inactive.png'/>")
		 .click(function()
			{
			    $(this).parent().parent().children(".dropdown").slideToggle();
			    $(this).attr("src", $(this).attr("src") == "img/dropdown-active.png" ? "img/dropdown-inactive.png" : "img/dropdown-active.png");
			    return false;
			});
	     var class_name = $("<span/>")
		 .text(curClass.name)
		 .addClass("class_id_"+curClass.id)
		 .css("color", curClass.color);
	     ul.append(class_entry);
	     class_entry.append(class_entry_div);
	     class_entry_div.append(dropdown_triangle).append(class_name);
	     
	     var instances_ul = $("<ul class='dropdown' style='display:none'/>");
	     class_entry.append(instances_ul);
	     
	     for (var j = 0; j < curClass.instances.length; j++)
	     {
		 // Call everything in its own function so that the variables scope right
		 (function()
		  {
		      var curInstance = curClass.instances[j];
		      var instance_li = $("<li/>")
			  .text(curInstance.name)
			  .addClass("instance_id_"+curInstance.id)
			  .addClass("instances_entry")
			  .css("color", curInstance.color)
			  .click(function()
				 {
				     fillMessagesByClass(curClass.id, curInstance.id);
				 });
		      instances_ul.append(instance_li);
		  })();
	     }
	 })();
    }
    root.html(ul);
};

var fillMessagesByClass = function(class_id, instance_id)
{
    var headerText = "all classes";
    var messagesOut;

    // Class is defined
    if (typeof(class_id) != 'undefined')
    {
	headerText += " >  " + classes[class_id].name;
	// Instance is defined
	if (typeof(instance_id) != 'undefined')
	{
	    headerText += " > " + instances[instance_id].name;
	    messagesOut = instances[instance_id].messages;
	}
	else
	{
	    messagesOut = classes[class_id].messages;
	}
    }
    // No class selected
    else
    {
	messagesOut = classes_messages;
    }

    // Actually fill in the messages
    $("#messages").html('');
    for (var i in messagesOut)
    {
	var message_entry = $("<div class='messages_entry'/>");
	var header = $("<div class='message_header'/>");
	var header_class = $("<span />")
	    .addClass("class_id_"+messagesOut[i].parent_class.id)
	    .css("color", messagesOut[i].parent_class.color)
	    .text(messagesOut[i].parent_class.name);
	var header_instance = $("<span />")
	    .addClass("instance_id_"+messagesOut[i].parent_instance.id)
	    .css("color", messagesOut[i].parent_instance.color)
	    .text(messagesOut[i].parent_instance.name)
        var header_sender = messagesOut[i].sender;
	header.append(header_class).append(" / ")
	    .append(header_instance).append(" / ")
	    .append(header_sender);
        var body = $("<div class='message_body'/>").text(messagesOut[i].message);
	message_entry.append(header).append(body);
	$("#messages").append(message_entry);
    }
    
    $("#chatheader").text(headerText);
};

var fillMessagesByPersonal = function(personal_id)
{
    var headerText = "personals";
    var messagesOut;

    // If we are looking a specific person
    if (personal_id)
    {
	// Do stuff
    }
    // See all personals
    else
    {
	messagesOut = personal_messages;
    }

    console.log("fillMessagesByPersonal");
    console.log(messagesOut);

    // Actually fill in the messages
    $("#messages").html('');
    for (var i in messagesOut)
    {
	console.log(messagesOut[i]);
	var message_entry = $("<div class='messages_entry'/>");
	var header = $("<div class='message_header'/>")
	    .text(messagesOut[i].sender);
        var body = $("<div class='message_body'/>").text(messagesOut[i].message);
	message_entry.append(header).append(body);
	$("#messages").append(message_entry);
    }

    $("#chatheader").text(headerText);
};