var messages = [
    {
	id: 0,
	parent_class: null,
	parent_instance: null,
      	message: "Hi Tim!",
	sender: 'gurtej',
	timestamp: '01-01-9999 21:59',
	recipient: null,
    },
    {
	id: 1,
	parent_class: null,
	parent_instance: null,
	message: "We should meet tomorrow",
	sender: 'mikewu',
	timestamp: '01-01-9999 21:59',
	recipient: null,
    },
    {
	id: 2,
	parent_class: null,
	parent_instance: null,
	message: "Nom nom nom babies",
	sender: 'garywang',
	timestamp: '01-01-9999 21:59',
	recipient: 'gurtej',
    },
    {
	id: 3,
	parent_class: null,
	parent_instance: null,
	message: "yay sipb",
	sender: 'timyang',
	timestamp: '02-05-9999 11:11',
	recipient: null,
    }
];

var instances = [
    {
	id: 0,
	name: "hello",
	last_messaged: '01-01-9999 21:59',
	color: "#ff9900",
	parent_class: null,
	messages: [messages[0]]
    },
    {
	id: 1,
	name: "meeting",
	last_messaged: '01-01-9999 21:59',
	color: "#cc6600",
	parent_class: null,
	messages: [messages[1]]
    },
    {
	id:2,
	name: "hooray",
	last_messaged: '02-04-9999 11:11',
	color: "#c66600",
	parent_class: null,
	messages: [messages[3]]
    }
];

var classes = [
    {
	id: 0,
	name: "zephyrplus",
	last_messaged: '01-01-9999 21:59',
	color: "#ffff00",
	instances: [instances[0], instances[1]],
	messages:[messages[0], messages[1]],
    },
    {
	id: 1,
	name: "sipb",
	last_messaged: '01-01-9999 21:59',
	color: "#0099ff",
	instances: [instances[2]],
	messages: [messages[3]],
    }
];

var personal_messages = [messages[2]];
var classes_messages = [messages[0], messages[1], messages[3]];

messages[0].parent_class = classes[0];
messages[0].parent_instance = instances[0];
messages[1].parent_class = classes[0];
messages[1].parent_instance = instances[1];
instances[0].parent_class = classes[0];
instances[1].parent_class = classes[0];

messages[3].parent_class = classes[1];
messages[3].parent_instance = instances[2];
instances[2].parent_class = classes[1];


var personals = [
    'gurtej',
    'timyang',
    'garywang',
    'mikewu',
    'zeidman',
    'mr.unknown',
    'ashketchup',
    'ruthie',
    'mprat',
    'pkoms',
    'taylors',
];

// TODO: Have functions to load all this data from the server
