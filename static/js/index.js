// When the document loads, populate the personals
$(document).ready(function()
{
    // Dealing with styling the sidebar
    $("#personals_sidebar").resizable({handles:'s',minHeight: 20});
    $("#personals_anchor").css({height:$("#personals_sidebar").height()-20});
    $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20});
				 
    $("#personals_sidebar").resize(function()
				  {
				      $("#personals_anchor").css({height:$("#personals_sidebar").height()-20});
				      $("#classes_sidebar").css({height:$("#dropdown").height()-$("#personals_sidebar").height()});
				      $("#classes_anchor").css({height:$("#dropdown").height()-$("#personals_sidebar").height()-20});
				  });    

    $("#classes_title").click(function()
			      {
				  fillMessagesByClass();
				  fillButtonArea();
			      });
    $("#personals_title").click(function()
				{
				    fillMessagesByPersonal();
				    fillButtonArea();
				});

    fillMessagesByClass();
    fillButtonArea();
    // Loading the personals and classes lists
    loadPersonals();
    loadClasses();

    // Setting the form submission handler
    $("#chatsend").submit(
	function(event)
	{
	    var messageTextArea = $(this).find("#messagetextarea");
	    var messageText = messageTextArea.val();
	    messageTextArea.val('');
	    var classDropDown = $(this).find("#classdropdown");
	    var classText = classes[classDropDown.val()].name;
	    var instanceDropDown = $(this).find("#instancedropdown");
	    var instanceId = instanceDropDown.val();
	    var instanceText;
	    if (instanceId == "new")
	    {
		instanceText = $(this).find("#instancetext").val();
	    }
	    else
	    {
		instanceText = instances[instanceId].name;
	    }

	    console.log("Vals: " + instanceText + " " + classText + " " + messageText);
	    console.log(event);

	    $.ajax({
		url: "/chat",
		data:
		{
		    'class': classText,
		    'instance': instanceText,
		    'message': messageText,
		},
		success: function()
		{
		    console.log("Success!");
		}
	    });
	    return false;
	});

    // Add class by clicking on "+"
    $("#add_class").click(
	function()
	{
	    addZephyrClass();
	});

    // Changes instances options on class selection change
    $("#classdropdown").change(
	function()
	{
	    fillInstancesDropDown();
	});

    // Hide/display the instance test box if "New instance" is selected
    $("#instancedropdown").change(
	function()
	{
	    console.log("Instance drop down changed");
	    console.log($(this).val());
	    if ($(this).val() == "new")
	    {
		$("#instancetext").show();
	    }
	    else
	    {
		$("#instancetext").hide();
	    }
	});
});

// Constant defining max number of personals to display in the sidebar
var maxPersonals = 5;

// Load the personals to display in the sidebar
var loadPersonals = function()
{
    // TODO: Make an AJAX call to get the personals data

    root = $("#personals_anchor");
    ul = $("<ul></ul>");

    for (var i = 0; i < personals.length; i++)
    {
	ul.append("<li>" + personals[i] + "</li>");
    }

    root.html(ul);
};

// Constant defining max number of classes to display in the sidebar
//var maxClasses = 5;

// Load the classes to display in the sidebar
var loadClasses = function()
{
    // TODO: Load the classes via AJAX

    var root = $("#classes_anchor");
    var ul = $("<ul></ul>");
    for (var i = 0; i < classes.length; i++)
    {
/*	if (i == maxClasses)
	{
	    break;
	}*/

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
			    fillButtonArea(curClass.id);
			});
	     var dropdown_triangle = $("<img src='/static/img/dropdown-inactive.png'/>")
		 .click(function()
			{
			    $(this).parent().parent().children(".dropdown").slideToggle();
			    $(this).attr("src", $(this).attr("src") == "/static/img/dropdown-active.png" ? "/static/img/dropdown-inactive.png" : "/static/img/dropdown-active.png");
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
				     fillButtonArea(curClass.id, curInstance.id);
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
    var allClassesHeader = $("<span/>")
	.text("all classes")
	.click(function()
	       {
		   fillMessagesByClass();
		   fillButtonArea();
	       });
    var headerText = $("#chatheader")
	.html(allClassesHeader)
	.off("click");
    var messagesOut;

    // Class is defined
    if (typeof(class_id) != 'undefined')
    {
	//	headerText += " >  " + classes[class_id].name;
	var headerText_class = $("<span />")
	    .addClass("class_id_"+classes[class_id])
	    .text(classes[class_id].name)
	    .click(function()
		   {
		       fillMessagesByClass(class_id);
		       fillButtonArea(class_id);
		   });
	headerText.append(" > ").append(headerText_class);
    	// Instance is defined
	if (typeof(instance_id) != 'undefined')
	{
//	    headerText += " > " + instances[instance_id].name;
	    var headerText_instance = $("<span />")
		.addClass("instance_id_"+instances[instance_id])
		.text(instances[instance_id].name)
		.click(function()
		       {
			   fillMessagesByClass(class_id, instance_id);
			   fillButtonArea(class_id, instance_id);
		       });
	    headerText.append(" > ").append(headerText_instance);
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
    for (var messageNum in messagesOut)
    {
	(function(){
	    var i = messageNum;
	    var message_entry = $("<div class='messages_entry'/>");
	    var header = $("<div class='message_header'/>");
	    var header_class = $("<span />")
		.addClass("class_id_"+messagesOut[i].parent_class.id)
		.css("color", messagesOut[i].parent_class.color)
		.text(messagesOut[i].parent_class.name)
		.click(function()
		       {
			   fillMessagesByClass(messagesOut[i].parent_class.id);
			   fillButtonArea(messagesOut[i].parent_class.id);
		       });
	    var header_instance = $("<span />")
		.addClass("instance_id_"+messagesOut[i].parent_instance.id)
		.css("color", messagesOut[i].parent_instance.color)
		.text(messagesOut[i].parent_instance.name)
		.click(function()
		       {
			   fillMessagesByClass(messagesOut[i].parent_class.id, messagesOut[i].parent_instance.id);
			   fillButtonArea(messagesOut[i].parent_class.id, messagesOut[i].parent_instance.id);
		       });
            var header_sender = messagesOut[i].sender;
	    header.append(header_class).append(" / ")
		.append(header_instance).append(" / ")
		.append(header_sender);
            var body = $("<div class='message_body'/>").text(messagesOut[i].message);
	    message_entry.append(header).append(body);
	    $("#messages").append(message_entry);
	})();
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

    // Actually fill in the messages
    $("#messages").html('');
    for (var i in messagesOut)
    {
	var message_entry = $("<div class='messages_entry'/>");
	var header = $("<div class='message_header'/>")
	    .text(messagesOut[i].sender);
        var body = $("<div class='message_body'/>").text(messagesOut[i].message);
	message_entry.append(header).append(body);
	$("#messages").append(message_entry);
    }

    $("#chatheader").text(headerText);
};

var fillButtonArea = function(class_id, instance_id)
{
    fillClassesDropDown(class_id);
    fillInstancesDropDown(instance_id);
};

var fillClassesDropDown = function(class_id)
{
    console.log("Filling classes drop down: " + class_id);
    // Clear the dropdown
    $("#classdropdown").html('');
    // Loop through the classes and add them
    for(var i = 0; i < classes.length; i++)
    {
	var curClass = classes[i];
	var option = $("<option/>")
	    .val(curClass.id)
	    .attr("id", "option_class_id_"+curClass.id)
	    .text(curClass.name);
	$("#classdropdown").append(option);
    }

    // If we're given a default class, make it selected
    if (typeof(class_id) != 'undefined')
    {
	var class_option = $("#option_class_id_"+class_id);
	class_option.attr('selected', true);
	selectedClass = class_id;
    }
};

var fillInstancesDropDown = function(instance_id)
{
    // Figure out which class is selected (or fill in a default if there isn't one)
    var selectedClass = 0;
    if (typeof($("#classdropdown").val()) != 'undefined')
    {
	selectedClass = $("#classdropdown").val();
    }

    // Clear the dropdown
    $("#instancedropdown").html('');
    // Loop through that class's instances and create an option for each one
    for(var i = 0; i < classes[selectedClass].instances.length; i++)
    {
	var curInstance = classes[selectedClass].instances[i];
	var option = $("<option/>")
	    .val(curInstance.id)
	    .attr("id", "option_instance_id_"+curInstance.id)
	    .text(curInstance.name);
	$("#instancedropdown").append(option);
    }
    // Add in the new instance option
    var option = $("<option/>")
	.val("new")
	.attr("id", "option_instance_id_new")
	.text("New instance");
    $("#instancedropdown").append(option);

    // If there's a particular default instance, make it selected
    if (typeof(instance_id) != 'undefined')
    {
	var instance_option = $("#option_instance_id_"+instance_id);
	instance_option.attr('selected', true);
    }
};

var addZephyrClass = function()
{
    var new_class_name = prompt("Please enter the class you want to add.");
    classes.push(
	{
	    id:classes.length,
	    name: new_class_name,
	    last_messaged: null,
//	    color: "#ffffff", //TODO: auto-generate this color
	    color: hashStringToColor(new_class_name),
	    instances: [],
	    messages: []
	});
    loadClasses();
    //TODO: make this actually add a class
};

function hashStringToColor(str){
    var sum=0;
    for(var n=0; n<str.length; n++){
        sum+=str.charCodeAt(n);
        sum*=17;
        sum%=32452843;
    }
    var colors=[0, 0, 0];
    for(var n=0; n<24; n++){
        colors[n%3]*=2;
        colors[n%3]+=sum%2;
        sum=Math.floor(sum/2);
    }
    colors=hsvToRgb(colors[0]/255, colors[1]/255, (colors[2]/255+1)/2); //Increase brightness
    var colorStr="#";
    for(var n=0; n<3; n++){
        var s=Math.floor(colors[n]).toString(16);
        colorStr+=(s.length==2) ? s : ("0"+s);
    }
    return colorStr;
}

function hsvToRgb(h, s, v){
    var r, g, b;

    var i = Math.floor(h * 6);
    var f = h * 6 - i;
    var p = v * (1 - s);
    var q = v * (1 - f * s);
    var t = v * (1 - (1 - f) * s);

    switch(i % 6){
        case 0: r = v, g = t, b = p; break;
        case 1: r = q, g = v, b = p; break;
        case 2: r = p, g = v, b = t; break;
        case 3: r = p, g = q, b = v; break;
        case 4: r = t, g = p, b = v; break;
        case 5: r = v, g = p, b = q; break;
    }

    return [r * 255, g * 255, b * 255];
}
