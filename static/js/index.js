// Set global variables
focused = true;
atBottom = false;

// When the document loads, populate the personals
$(document).ready(function()
{
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
	// Set a flag so that onzephyr can perform setup functions
	needsToBeSetup = true;

	// If the user is first logging in, initialize their data
	if (api.storage.last_logged_in == undefined)
	{
	    // Create a storage object with some structure
	    api.storage =
		{
		    // When did the user last log in
		    last_logged_in: new Date(),
		    // Which instance and class was the user last viewing
		    last_viewed:
		    {
			instance: undefined,
			cls: undefined,
			type: 0,
		    },
		    // A dictionary of instances and when we last viewed their messages
		    instances_last_seen: {}
		}
        
        // Give the user a popup telling them to see help
        setTimeout("alert('New to Zephyr? See the help section for more information on how Zephyr works and how to use ZephyrPlus');", 0);
	}
	// If the user already has a storage, set some values, and check consistency
	else
	{
	    // Set last_logged_in
	    api.storage.last_logged_in = new Date();

	    // Check last_viewed
	    if (!api.storage.last_viewed)
	    {
		api.storage.last_viewed =
		    {
			instance: undefined,
			cls: undefined,
			type: 0,
		    };
	    }
	    else if (api.storage.last_viewed.type == undefined)
		{
		    api.storage.last_viewed.type = 0;
	    }
	}
        $("#logged_user")
            .text(api.username);
    };
    api.onzephyr = function(zephyrs)
    {
	// Only perform this setup on the very first onzephyr call
	if (needsToBeSetup)
	{
	    // Check for first login
	    if (api.storage.last_logged_in == undefined)
	    {		
		// Initialize the instances_last_seen dictionary
		for (var i = 0; i < api.instances.length; i++)
		{
		    var curInstance = api.instances[i];
		    api.storage.instances_last_seen[curInstance.id] = (new Date()).getTime();
		}
	    }
	    else
	    {
		// Check instances_last_seen
		for (var i = 0; i < api.instances.length; i++)
		{
		    if (!(typeof api.storage.instances_last_seen[api.instances[i].id] == 'number'))
		    {
			api.storage.instances_last_seen[api.instances[i].id] = 0;
		    }
		}
	    }
		

            // Fill in the messages and button area
    	    fillMessagesByClass(api.storage.last_viewed.cls, api.storage.last_viewed.instance);
            fillButtonArea(api.storage.last_viewed.cls, api.storage.last_viewed.instance);
            // Fill in the personals and classes sidebar
            //fillPersonals(); // Personals don't exist anymore
            fillClasses();
	    // Scroll to the bottom of the messages div
	    //$("#messages_scroll").prop({ scrollTop: $("#messages_scroll").prop("scrollHeight") });
        }


        var curViewModified = false;
       
        var missed = [];
	// Determine whether the message would be displayed in the current view
	// Dynamically update if it would; otherwise add it to missed messages
	for (var i = 0; i < zephyrs.length; i++)
	{
	    curZephyr = zephyrs[i];
	    // If we're in the class view, compare class id and instance id
	    if (!needsToBeSetup && api.storage.last_viewed.type == 0 && (curZephyr.parent_class.id == api.storage.last_viewed.cls || api.storage.last_viewed.cls == undefined) && (curZephyr.parent_instance.id == api.storage.last_viewed.instance || api.storage.last_viewed.instance == undefined))
	    {
		// Add the zephyr to our view
		var messageEntry = createMessage(curZephyr);
		$("#messages").append(messageEntry);
		curViewModified = true;
		// If the tab isn't focused add it to a missed messages
		if (!focused || !atBottom)
		{
		    addMissedMessage(curZephyr);
                    missed.push(curZephyr);
		    //setTitle(1);
		}
	    }
	    // If we're in the personal view, we don't do this!
	    else if (!needsToBeSetup && api.storage.last_viewed.type == 1)
	    {
		// ERROR: We don't do this
		console.log("Error: trying to add a personal");
	    }
	    else
	    {
		addMissedMessage(curZephyr);
                missed.push(curZephyr);
		if (!focused) // If the tab isn't focused set the title
		{
		    //setTitle(1);
		}
	    }
	}
	if(missed.length>0)
            showNotifications(missed);

	// Scroll to the bottom of the messages div
	if (atBottom && curViewModified && focused)
	{
	    $("#messages_scroll").animate({ scrollTop: $("#messages_scroll").prop("scrollHeight") }, 1000);
	}

	// Update the missed messages counters
	updateMissedMessages();

	needsToBeSetup = false;
    };

    
    var scrolled = false;
    // Check for scrolled to bottom
    $("#messages_scroll").scroll(function()
    {
        atBottom = ($("#messages_scroll").prop("scrollHeight") - ($("#messages_scroll").height() + $("#messages_scroll").scrollTop())<20);
        // Mark all messages in current class as read if we're at the bottom
        if (atBottom && api.storage && api.storage.last_viewed)
        {
            setCurrentRead(api.storage.last_viewed.cls, api.storage.last_viewed.instance);
        }
        scrolled = true;
    });
    api.onstatuschange=function(status){
        if(status == api.UPDATESUGGESTED){
            $("<div>").html("ZephyrPlus has been updated!  Refresh the page to update to the latest version!")
                      .dialog({
                          buttons: {
                              "Refresh now": function(){
                                  location.reload();
                              },
                              "Refresh later": function(){
                                  $(this).dialog("close");
                              }
                          }
                      });
        }
        else if(status == api.UPDATEREQUIRED){
            location.reload();
        }
    }
    
    function processScroll(){
        if(scrolled){
            scrolled = false;
            var classId = api.storage.last_viewed.cls;
            var instanceId = api.storage.last_viewed.instance;
            if(!api.storage.first_visible)
                api.storage.first_visible = {};
            var name = "";
            if(instanceId)
                name = "instance"+instanceId;
            else if(classId)
                name = "class"+classId;
            var messages = $("#messages .messages_entry");
            var a=0, b=messages.length;
            while(b>a){
                var c = Math.floor((a+b)/2);
                var position = $(messages[c]).position().top;
                if(position<0)
                    a=c+1;
                else
                    b=c;
            }
            if(messages[a])
                api.storage.first_visible[name] = messages[a].id.substr(7); //"message"
        }
        window.setTimeout(processScroll, 500);
    }
    processScroll();
    
    window.setInterval(api.saveStorage, 5*60*1000);
    
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
		       'signature': api.storage.signature,
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
	    function(e) {
		addZephyrClass();
		e.stopPropagation();	//Don't switch back to the default view
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
	    this.value=wrapStr(this.value);
	}
    ).keyup(
	function() {
	    var lines=this.value.split("\n");
	    if(lines.length>2 && lines[lines.length-2]=="." && lines[lines.length-1]==""){
		lines.length-=2;
		this.value=lines.join("\n");
		$("#messagetextarea").change();
		$("#chatsend").submit();
	    }
	}
    );
    
    $("#settings_link").click(showSettings);
    
    $("#mark_read").click(markAllAsRead);


});


// Set the focus and blur handlers to modify a global flag
$(window).focus(function() { focused = true; });
$(window).blur(function() { focused = false; });


var updateTitle = function()
{
    var numMissed = 0;
    for (var i = 0; i < api.instances.length; i++)
    {
	numMissed += api.instances[i].missedMessages.length;
    }
    $(document).attr("title", (numMissed==0) ? "ZephyrPlus!" : "ZephyrPlus! ("+numMissed+")");
    if(numMissed > 0 && api.storage.last_viewed && !api.storage.last_viewed.cls)
        $("#mark_read").show();
    else
        $("#mark_read").hide();
};

var setCurrentRead = function(class_id, instance_id)
{
    // Get the objects
    var instanceObj = api.getInstanceById(instance_id);
    var classObj = api.getClassById(class_id);

    // Class id defined
    if (classObj)
    {
	// Instance is defined
	if (instanceObj)
	{
	    // Clear missed messages for this instance
	    instanceObj.missedMessages = [];
	    updateClassMissedMessages(classObj);
	    updateInstanceMissedMessages(instanceObj);
            api.storage.instances_last_seen[instance_id] = (new Date()).getTime();
	}
	else
	{
	    // Clear missed messages for the class
	    for (var i = 0; i < classObj.instances.length; i++)
	    {
		classObj.instances[i].missedMessages = [];
                api.storage.instances_last_seen[classObj.instances[i].id] = (new Date()).getTime();
	    }
	    updateClassMissedMessages(classObj);
	}
    }
    updateTitle();
}

function markAllAsRead(){
    for(var n=0; n<api.instances.length; n++){
        setCurrentRead(api.instances[n].parent_class.id, api.instances[n].id);
    }
    api.storage.first_visible = {};
    updateMissedMessages();
    api.saveStorage();
}

var addMissedMessage = function(message)
{
    if (!message.parent_class || !message.parent_instance)
    {
	// We need to have both (since we don't deal with personals)
	return -1;
    }

    // Check that the message is actually after the last seen time for the instance
    if (api.storage.instances_last_seen[message.parent_instance.id] < message.timestamp.getTime())
    {
	message.parent_class.missedMessages.push(message);
	message.parent_instance.missedMessages.push(message);
    }
}

var oldNote = false;
function showNotifications(messages){
    if(!needsToBeSetup && 
            api.storage.notify && 
            webkitNotifications && 
            webkitNotifications.checkPermission()==0){
        if(oldNote){
            oldNote.note.cancel();
            window.clearTimeout(oldNote.timeout);
            oldNote = false;
        }
        
        var title, body;
        if(messages.length == 1){
            var message = messages[0];
            title = "New Zephyr to " + message.parent_class.name + "/" + message.parent_instance.name
                + " from " + message.sender;
            body = message.message_body;
        }
        else{
            var classesDict = {};
            for(var n=0; n<messages.length; n++)
                classesDict[messages[n].parent_class.name] = true;
            var classes = [];
            for(name in classesDict)
                classes.push(name);
            title = messages.length + " new Zephyrs to class ";
            if(classes.length == 1)
                title += classes[0];
            else if(classes.length == 2)
                title += classes[0] + " and " + classes[1];
            else
                title += classes.slice(0, -1).join(", ") + ", and " + classes[classes.length-1];
            body = "";
        }
        
        var note = webkitNotifications.createNotification(
            "/static/img/zp_logo.png",
            title,
            body
        );
        note.onclick = function(){
            note.cancel();
            window.focus();
        }
        note.show();
        oldNote = {
            note: note,
            timeout: window.setTimeout(function(){
                note.cancel();
            }, 5000)
        };
    }
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
    updateTitle();
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
			 var name1 = c1.name, name2 = c2.name;
			 var un1=false, un2=false;
			 if (name1.indexOf("un") == 0) { name1=name1.substr(2); un1=true; }
			 if (name2.indexOf("un") == 0) { name2=name2.substr(2); un2=true; }
			 if (name1 > name2) { return 1; }
			 else if (name1 < name2) { return -1; }
			 else if (un1 && !un2) { return 1; }
			 else if (un2 && !un1) { return -1; }
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
							$("#classes_entry_id_"+curClass.id).parent().remove();
							if(typeof(api.storage.last_viewed.cls) == 'undefined' ||
								api.storage.last_viewed.cls == curClass.id)
							    fillMessagesByClass();
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
			  //.addClass("instance_id_"+curInstance.id)
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
    if(typeof(message.element) != "undefined")
	return message.element;
    var classObj = message.parent_class;
    var instanceObj = message.parent_instance;
    var sender_text = message.sender;
    var message_text = message.message_body;
    var signature = message.signature;
    var timestamp = message.timestamp;
    var auth = message.auth;
    var message_entry = $("<div class='messages_entry'/>")
	.click(function()
	       {
		   fillButtonArea(classObj.id, instanceObj.id);
		   $("#messagetextarea").focus();
	       })
        .prop("id", "message"+message.id);
    var header = $("<div class='message_header'/>");
    var header_class = $("<span />")
	//.addClass("class_id_"+classObj.id)
	.css("color", classObj.color)
        .css("cursor", "pointer")
	.text(classObj.name)
	.click(function()
	       {
		   fillMessagesByClass(classObj.id);
		   fillButtonArea(classObj.id);
	       });
    var header_instance = $("<span />")
	//.addClass("instance_id_"+instanceObj.id)
	.css("color", instanceObj.color)
        .css("cursor", "pointer")
	.text(instanceObj.name)
	.click(function()
	       {
		   fillMessagesByClass(classObj.id, instanceObj.id);
		   fillButtonArea(classObj.id, instanceObj.id);
	       });

    // Makes sender name brighter.
    sender_text = "<span class='sender'>"+sender_text+"</span>";
    
    var links = message_text.match(/https?:\/\/[^ '"\n]+/g);

    if(!auth)
	sender_text += " <span class='unauth'>(UNAUTH)</span>";
    
    if(signature)
        sender_text+=" ("+signature+")";
    header.append(header_class).append(" / ")
	.append(header_instance).append(" / ")
	.append(sender_text)
        .append($("<span class='message_timestamp'/>").text(convertTime(timestamp)));
    var body = $("<pre class='message_body'/>").text(message_text);
    if(links)
        for(var n=0; n<links.length; n++)
            body.html(body.html().replace(links[n], "<a href=\""+links[n]+"\" target=\"_blank\">"+links[n]+"</a>"));
	body.html(formatText(body.html()));
    message_entry.append(header, body);
    message.element = message_entry;
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
    var classObj = api.getClassById(class_id);
    var instanceObj = api.getInstanceById(instance_id);
    
    if (class_id && !classObj)
        return fillMessagesByClass();
    else if (instance_id && !instanceObj)
        return fillMessagesByClass(class_id);
	
    // Set storage variables and save storage
    api.storage.last_viewed.cls = class_id;
    api.storage.last_viewed.instance = instance_id;
    api.storage.last_logged_in = (new Date()).getTime();
    api.storage.last_viewed.type = 0;

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

    $(".classes_entry.selected").removeClass("selected");
    $(".instances_entry.selected").removeClass("selected");

    // Class is defined
    if (typeof(class_id) != 'undefined')
    {
	var headerText_class = $("<span />")
	    //.addClass("class_id_"+classObj.name)
	    .text(classObj.name)
	    .css("cursor", "pointer")
	    .click(function()
		   {
		       fillMessagesByClass(class_id);
		       fillButtonArea(class_id);
		   });
	headerText.append(" > ").append(headerText_class);
	
	var selected = $("#classes_entry_id_"+class_id);
	if(selected.length==0){
	    fillClasses();
	    selected = $("#classes_entry_id_"+class_id);
	}
	selected.addClass("selected");
	if(selected.position().top < 0 || selected.position().top > selected.offsetParent().height()-50){
	    if(selected.position().top < 0)
		selected.offsetParent().scrollTop(selected.offsetParent().scrollTop()+selected.position().top-selected.offsetParent().height()/10);
	    else
		selected.offsetParent().scrollTop(selected.offsetParent().scrollTop()+selected.position().top-selected.offsetParent().height()/2);
	}

	// Instance is defined
	if (instance_id != undefined)
	{
	    var headerText_instance = $("<span />")
		//.addClass("instance_id_"+instanceObj.name)
		.text(instanceObj.name)
		.css("cursor", "pointer")
		.click(function()
		       {
			   fillMessagesByClass(class_id, instance_id);
			   fillButtonArea(class_id, instance_id);
		       });
	    headerText.append(" > ").append(headerText_instance);
	    messagesOut = instanceObj.messages;
	    
	    var selected = $("#instances_entry_id_"+instance_id);
	    if(selected.length==0){
		fillClasses();
		selected = $("#instances_entry_id_"+instance_id);
	    }
	    selected.addClass("selected");
	    if(selected.position().top < 0 || selected.position().top > selected.offsetParent().height()-50){
		if(selected.position().top < 0)
		    selected.offsetParent().scrollTop(selected.offsetParent().scrollTop()+selected.position().top-selected.offsetParent().height()/10);
		else
		    selected.offsetParent().scrollTop(selected.offsetParent().scrollTop()+selected.position().top-selected.offsetParent().height()/2);
	    }
	    
	}
	else
	{
	    messagesOut = classObj.messages;
	}	    

	// Set the messages to read
	setCurrentRead(class_id, instance_id);
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
    $(".messages_entry").detach();
    $("#messages").html('');

    // Display "no zephyrs" if there are no zephyrs in the class.
    if (messagesOut.length == 0)
    {
	(function(){
	    $("#messages").append("<br /><i>(No Zephyrs from the past three days.)</i>");
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
    // $("#messages").prop({ scrollTop: $("#messages").prop("scrollHeight") });
    
    if(api.storage.first_visible){
        var first;
        if(instance_id)
            first = api.storage.first_visible['instance'+instance_id];
        else if(class_id)
            first = api.storage.first_visible['class'+class_id];
        else
            first = api.storage.first_visible[''];
        if(!first && api.storage.instances_last_seen);
        if(first && $("#message"+first).length>0)
            $("#messages_scroll").scrollTop($("#messages_scroll").scrollTop()+$("#message"+first).position().top);
        else
            //$("#messages-scroll").scrollTop(0);
            $("#messages_scroll").scrollTop($("#messages_scroll").prop("scrollHeight"));
    }
    
    $("#chatheader").text(headerText);
    
    api.saveStorage();
    updateTitle();
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
        api.addSubscription(new_class_name, undefined, undefined, function(){
	    fillClasses();
	    updateMissedMessages();
	    fillMessagesByClass(api.classDict[new_class_name].id);
	});
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
    if(!len)
	len=65;
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

/* Formats text according to formatting in Zephyr */
function formatText(str){
	var fText = str;
	fText = replaceZephyrTag("b", "b", fText);
	fText = replaceZephyrTag("bold", "b", fText);
	fText = replaceZephyrTag("i", "i", fText);
	fText = replaceZephyrTag("italic", "i", fText);
	//fText = replaceZephyrTag("big", "big", fText);
	//fText = replaceZephyrTag("small", "small", fText);

	return fText;
}

/* Replace zephyr tags with html tags */
function replaceZephyrTag(zephyrTag, htmlTag, str) {
	var regex1 = RegExp("@" + zephyrTag + "\\{([^\\}]*)\\}", "g");
	var regex2 = RegExp("@" + zephyrTag + "\\[([^\\]]*)\\]", "g");
	var regex3 = RegExp("@" + zephyrTag + "\\(([^\\)]*)\\)", "g");

	openTag = "<" + htmlTag + ">";
	closeTag = "</" + htmlTag + ">";

	var rText = str;
	if(rText.match(regex1)){
		rText = rText.replace(regex1, openTag + "$1" + closeTag);
	} else if(rText.match(regex2)){
		rText = rText.replace(regex2, openTag + "$1" + closeTag);
	} else if(rText.match(regex3)){
		rText = rText.replace(regex3, openTag + "$1" + closeTag);
	}

	return rText;
}

var settingsDialog;
function showSettings(){
    if(settingsDialog){
        settingsDialog.dialog("open");
        return;
    }
    
    var form = $("<form/>");
    
    if(webkitNotifications){
        var notifyOn = $("<input type='radio' name='notify' id='notifyOn' value='on'/>");
        var notifyOff = $("<input type='radio' name='notify' id='notifyOff' value='off'/>");
        var notifySettings = $("<div>");
        notifySettings.append(
            "Desktop notifications:<br/>",
            notifyOn,
            "<label for='notifyOn'>On</label><br/>",
            notifyOff,
            "<label for='notifyOff'>Off</label><br/>"
        );
        if(api.storage.notify)
            notifyOn[0].checked=true;
        else
            notifyOff[0].checked=true;
        form.append(notifySettings);
        if(webkitNotifications.checkPermission() != 0){
            notifySettings.hide();
            var enableNotify = $("<input type='button' value='Enable desktop notifications'/>");
            enableNotify.click(function(){
                webkitNotifications.requestPermission(function(){
                    if(webkitNotifications.checkPermission() == 0){
                        enableNotify.hide();
                        notifySettings.show();
                        notifyOn[0].checked=true;
                    }
                });
            });
            form.append(enableNotify, "<br/>");
        }
        form.append("<br/>");
    }
    
    var signatureInput = $("<input type='text'>").val(api.storage.signature || "");
    form.append(
        "Signature<br/>",
        signatureInput,
        "<br/><br/>"
    );
    
    function save(){
        if(notifyOn)
            api.storage.notify=notifyOn[0].checked;
        if(signatureInput.val())
            api.storage.signature=signatureInput.val();
        else
            delete api.storage.signature;
        api.saveStorage();
        form.dialog("close");
    }
    
    function cancel(){
        form.dialog("close");
    }
    
    form.append(
        $("<input type='button' value='Save' />")
            .click(save),
        $("<input type='button' value='Cancel' />")
            .click(cancel)
    ).submit(function(e){
        e.preventDefault();
        save();
    });
    
    form.dialog({title: "Settings"});
    settingsDialog=form;
}
