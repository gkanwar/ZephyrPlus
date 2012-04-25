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

    //Dropdown 'class' header loads all classes upon clicking.
    $("#classestitleheader")
	.click(function()
	       {
		   fillMessagesByClass();
		   fillButtonArea();
	       })
	.css("cursor", "pointer");

    // Create the API object and define the callbacks
    api = new ZephyrAPI();
    api.onready = function()
    {
	needsToBeSetup = true;
    };
    api.onzephyr = function(zephyrs)
    {
	// Only perform this setup on the very first onzephyr call
	if (needsToBeSetup) 
	{
	    // Set some global variables
	    curView = 0; // 0 = Class view, 1 = Personal view
	    curClass = null;
	    curInstance = null;
	    curPersonal = null;
	    
            // Fill in the messages and button area
    	    fillMessagesByClass();
            fillButtonArea();
            // Fill in the personals and classes sidebar
            //fillPersonals(); // Personals don't exist anymore
            fillClasses();
	    // Scroll to the bottom of the messages div
	    $("#messages").prop({ scrollTop: $("#messages").prop("scrollHeight") });
        }

	// Determine whether the message would be displayed in the current view
	// Dynamically update if it would;
	// TODO: otherwise do something (bold + nums in parens)
	for (var i = 0; i < zephyrs.length; i++)
	{
	    curZephyr = zephyrs[i];
	    // If we're in the class view, compare class id and instance id
	    if (!needsToBeSetup && curView == 0 && (curZephyr.parent_class.id == curClass || typeof(curClass) == 'undefined') && (curZephyr.parent_instance.id == curInstance || typeof(curInstance) == 'undefined'))
	    {
		// Add the zephyr to our view
		var messageEntry = createMessage(curZephyr);
		$("#messages").append(messageEntry);
	    }
	    // If we're in the personal view, we don't do this!
	    else if (!needsToBeSetup && curView == 1)
	    {
		// ERROR: We don't do this
		console.log("Error: trying to add a personal");
	    }
	    else
	    {
		addMissedMessage(curZephyr);
	    }
	}

	// Scroll to the bottom of the messages div
	$("#messages").animate({ scrollTop: $("#messages").prop("scrollHeight") }, 1000);

	//Load logged in username
	$("#logged_user")
	    .text(api.username);

	// Update the missed messages counters
	updateMissedMessages();

	needsToBeSetup = false;
    };

    // Setting the form submission handler
    $("#chatsend").submit(
	function(event)
	{
	    var messageTextArea = $(this).find("#messagetextarea");
	    var messageText = messageTextArea.val();
	    messageTextArea.val('');
	    var classDropDown = $(this).find("#classdropdown");
	    var classText = api.getClassById(classDropDown.val()).name;
	    var instanceDropDown = $(this).find("#instancedropdown");
	    var instanceId = instanceDropDown.val();
	    var instanceText;
	    if (instanceId == "new")
	    {
		instanceText = $(this).find("#instancetext").val();
		if (instanceText == "")
		{
		    alert('Please enter an instance (subject) for your message!');
		    return false;
		}
	    }
	    else
	    {
		instanceText = api.getInstanceById(instanceId).name;
	    }

	    $.post("/chat",
		   {
		       'class': classText,
		       'instance': instanceText,
		       'message': messageText,
		   },
		   function()
		   {
		       console.log("Success!");
		   }
		  );
	    return false;
	}
    );

    // Add class by clicking on "+"
    $("#add_class")
	.css("cursor","pointer")
	.click(
	function() {
	    addZephyrClass();
	});

    // Changes instances options on class selection change
    $("#classdropdown").change(
	function() {
	    fillInstancesDropDown();
	}
    );

    // Hide/display the instance test box if "New instance" is selected
    $("#instancedropdown").change(
	function() {
	    if ($(this).val() == "new")
	    {
		$("#instancetext").show();
	    }
	    else
	    {
		$("#instancetext").hide();
	    }
	}
    );

    $("#messagetextarea").change(
	function() {
	    this.value=wrapStr(this.value, 72);
	}
    );


});




var addMissedMessage = function(message)
{
    if (!message.parent_class || !message.parent_instance)
    {
	// We need to have both (since we don't deal with personals)
	return -1;
    }
    
    message.parent_class.missedMessages.push(message);
    message.parent_instance.missedMessages.push(message);
};

var updateMissedMessages = function()
{
    for (var i = 0; i < api.classes.length; i++)
    {
	var curClass = api.classes[i];
	updateClassMissedMessages(curClass);
	for (var j = 0; j < curClass.instances.length; j++)
	{
	    updateInstanceMissedMessages(curClass.instances[j]);
	}
    }
};

var updateClassMissedMessages = function(classObj)
{
    // Compute the number of missed messages in the class
    var numMissed = 0;
    for (var i = 0; i < classObj.instances.length; i++)
    {
	numMissed += classObj.instances[i].missedMessages.length;
    }

    if (numMissed != 0)
    {
	$("#classes_entry_id_"+classObj.id)
	    .children(".class_text")
	    .text(classObj.name+" ("+numMissed+")")
	    .addClass("missed_messages");
    }
    else
    {
	$("#classes_entry_id_"+classObj.id)
	    .children(".class_text")
	    .text(classObj.name)
	    .removeClass("missed_messages");
    }
};

var updateInstanceMissedMessages = function(instanceObj)
{
    // Get the number of missed messages in the instance
    var numMissed = instanceObj.missedMessages.length;

    if (numMissed != 0)
    {
	$("#instances_entry_id_"+instanceObj.id)
	    .text(instanceObj.name+" ("+numMissed+")")
	    .addClass("missed_messages");
    }
    else
    {
	$("#instances_entry_id_"+instanceObj.id)
	    .text(instanceObj.name)
	    .removeClass("missed_messages");
    }
};
	

// Constant defining max number of personals to display in the sidebar
var maxPersonals = 5;

// Fill the personals in the sidebar
/* PERSONALS DON'T EXIST ANYMORE
var fillPersonals = function()
{
    root = $("#personals_anchor");
    ul = $("<ul></ul>");

    for (var i = 0; i < personals.length; i++)
    {
	ul.append("<li>" + personals[i] + "</li>");
    }

    root.html(ul);
};
*/

// Constant defining max number of classes to display in the sidebar
//var maxClasses = 5;

// Load the classes to display in the sidebar
var fillClasses = function()
{
    var root = $("#classes_anchor");
    var ul = $("<ul></ul>");
    api.classes.sort(function(c1, c2)
		     {
			 if (c1.name > c2.name) { return 1; }
			 else if (c1.name < c2.name) { return -1; }
			 else { return 0; }
		     });
    for (var i = 0; i < api.classes.length; i++)
    {
/*	if (i == maxClasses)
	{
	    break;
	}*/

	// Call everything in its own function to make it scope right
	(function()
	 {
	     var curClass = api.classes[i];
	     var class_entry = $("<li/>");
	     var class_entry_div = $("<div/>")
		 .attr("id", "classes_entry_id_"+curClass.id)
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
		 .addClass("class_text")
		 .css("cursor", "pointer")
		 .css("color", curClass.color);
	     var remove_class = $("<span/>")
		 .text('X')
		 .click(function(e)
			{
			    api.removeSubscription(curClass.name, undefined, undefined, 
						   function()
						   {
						       console.log('Removed subscription, killing HTML: ');
						       console.log($("#classes_entry_id_"+curClass.id));
						       $("#classes_entry_id_"+curClass.id).parent().remove();
						   }
						   );
                            e.stopPropagation(); //Don't switch to the class after removing it
			})
		 .addClass("remove_class");
	     ul.append(class_entry);
	     class_entry.append(class_entry_div);
	     class_entry_div
		 .append(dropdown_triangle)
		 .append(class_name)
		 .append(remove_class);
	     
	     var instances_ul = $("<ul class='dropdown' style='display:none'/>");
	     class_entry.append(instances_ul);
	     
	     curClass.instances.sort(function(i1, i2)
				     {
					 if (i1.name > i2.name) { return 1; }
					 else if (i1.name < i2.name) { return -1; }
					 else { return 0; }
				     });
	     for (var j = 0; j < curClass.instances.length; j++)
	     {
		 // Call everything in its own function so that the variables scope right
		 (function()
		  {
		      var curInstance = curClass.instances[j];
		      var instance_li = $("<li/>")
			  .attr("id", "instances_entry_id_"+curInstance.id)
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

var createMessage = function(message)
{
    var classObj = message.parent_class;
    var instanceObj = message.parent_instance;
    var sender_text = message.sender;
    var message_text = message.message_body;
    var signature = message.signature;
    var timestamp = message.timestamp;
    var message_entry = $("<div class='messages_entry'/>")
	.click(function()
	       {
		   fillButtonArea(classObj.id, instanceObj.id);
		   $("#messagetextarea").focus();
	       });
    var header = $("<div class='message_header'/>");
    var header_class = $("<span />")
	.addClass("class_id_"+classObj.id)
	.css("color", classObj.color)
        .css("cursor", "pointer")
	.text(classObj.name)
	.click(function()
	       {
		   fillMessagesByClass(classObj.id);
		   fillButtonArea(classObj.id);
	       });
    var header_instance = $("<span />")
	.addClass("instance_id_"+instanceObj.id)
	.css("color", instanceObj.color)
        .css("cursor", "pointer")
	.text(instanceObj.name)
	.click(function()
	       {
		   fillMessagesByClass(classObj.id, instanceObj.id);
		   fillButtonArea(classObj.id, instanceObj.id);
	       });

    // Makes sender name brighter.
    sender_text = "<span id=sender>"+sender_text+"</span>";

    if(signature)
        sender_text+=" ("+signature+")";
    header.append(header_class).append(" / ")
	.append(header_instance).append(" / ")
	.append(sender_text)
        .append($("<span class='message_timestamp'/>").text(convertTime(timestamp)));
    var body = $("<pre class='message_body'/>").text(message_text);
    message_entry.append(header, body);
    return message_entry
}

function convertTime(timestamp)
{
    var month = timestamp.getMonth()+1;
    var day = timestamp.getDate()

    var hours = timestamp.getHours()
    var minutes = timestamp.getMinutes()

    var suffix = "AM";
    if (hours >= 12) {
	suffix = "PM";
	hours = hours - 12;
    }

    if (hours == 0) {
	hours = 12;
    }
	
    if (minutes < 10){
	minutes = "0" + minutes
    }

    return month+"/"+day+" "+hours+":"+minutes+" "+suffix;
}

var fillMessagesByClass = function(class_id, instance_id)
{
    // Set global variables
    curClass = class_id;
    classObj = api.getClassById(class_id);
    curInstance = instance_id;
    instanceObj = api.getInstanceById(instance_id);
    curView = 0;
	
    var allClassesHeader = $("<span/>")
	.text("all classes")
	.css("cursor", "pointer")
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
	    .addClass("class_id_"+classObj.name)
	    .text(classObj.name)
	    .css("cursor", "pointer")
	    .click(function()
		   {
		       fillMessagesByClass(class_id);
		       fillButtonArea(class_id);
		   });
	headerText.append(" > ").append(headerText_class);
    	// Instance is defined
	if (typeof(instance_id) != 'undefined')
	{
	    // Clear missed messages for this instance
	    instanceObj.missedMessages = [];
	    updateClassMissedMessages(classObj);
	    updateInstanceMissedMessages(instanceObj);

	    var headerText_instance = $("<span />")
		.addClass("instance_id_"+instanceObj.name)
		.text(instanceObj.name)
		.css("cursor", "pointer")
		.click(function()
		       {
			   fillMessagesByClass(class_id, instance_id);
			   fillButtonArea(class_id, instance_id);
		       });
	    headerText.append(" > ").append(headerText_instance);
	    messagesOut = instanceObj.messages;
	}
	else
	{
	    // Clear missed messages for the class
	    for (var i = 0; i < classObj.instances.length; i++)
	    {
		classObj.instances[i].missedMessages = [];
	    }
	    updateClassMissedMessages(classObj);
	    messagesOut = classObj.messages;
	}
    }
    // No class selected
    else
    {
	messagesOut = api.messages;
    }

    // Sort the messages
    messagesOut.sort(function(m1, m2)
		     {
			 if (m1.timestamp > m2.timestamp) { return 1; }
			 else if (m1.timestamp < m2.timestamp) { return -1; }
			 else { return 0; }
		     });

    // Actually fill in the messages
    $("#messages").html('');

    // Display "no zephyrs" if there are no zephyrs in the class.
    if (messagesOut.length == 0)
    {
	(function(){
	    $("#messages").append("no zephyrs");
	})();
    }

    for (var messageNum in messagesOut)
    {
	(function(){
	    var i = messageNum;
	    var message_entry = createMessage(messagesOut[i]);
	    $("#messages").append(message_entry);
	})();
    }

    // Scroll to the bottom of the messages div
    $("#messages").prop({ scrollTop: $("#messages").prop("scrollHeight") });
    
    $("#chatheader").text(headerText);
};

var fillMessagesByPersonal = function(personal_id)
{
	// Set a global variable
	curPersonal = personal_id;
	curView = 1;
	
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
    // Clear the dropdown
    $("#classdropdown").html('');
    // Loop through the classes and add them
    for(var i = 0; i < api.classes.length; i++)
    {
	var curClass = api.classes[i];
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
    for(var i = 0; i < api.getClassById(selectedClass).instances.length; i++)
    {
	var curInstance = api.getClassById(selectedClass).instances[i];
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

    // Check for the new instance option being selected
    if ($("#instancedropdown").val() == "new")
    {
	$("#instancetext").show();
    }
    else
    {
	$("#instancetext").hide();
    }

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
    if(new_class_name == undefined){
        return;
    }

    new_class_name = new_class_name.replace(/^\s+|\s+$/g, '');
    if(new_class_name != "" && api.classDict[new_class_name] == undefined) {
        api.addSubscription(new_class_name, undefined, undefined, fillClasses);
    }
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

function wrapStr(str, len){
    var arr = str.split("\n");
    for(var n=0; n<arr.length; n++){
	if(arr[n].length>len){
	    var words=arr[n].split(" ");
	    arr[n]="";
	    var line="", lines=[];
	    for(var i=0; i<words.length; i++){
		if(line.length+words[i].length+1>len && line.length>0){
		    lines.push(line);
		    line="";
		}
		while(words[i].length>len){
		    lines.push(words[i].substr(0, len));
		    words[i]=words[i].substr(len);
		}
		line+=(line.length>0?" ":"")+words[i];
	    }
	    if(line.length>0)
		lines.push(line);
	    arr[n]=lines.join("\n");
	}
    }
    return arr.join("\n");
}
