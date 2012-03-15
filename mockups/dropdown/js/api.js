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
	instances: [],
	messages: [],
    }
];

messages[0].parent_class = classes[0];
messages[0].parent_instance = instances[0];
messages[1].parent_class = classes[0];
messages[1].parent_instance = instances[1];
instances[0].parent_class = classes[0];
instances[1].parent_class = classes[0];

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
