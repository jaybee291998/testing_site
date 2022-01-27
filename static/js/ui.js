const months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function showDivBase(div_to_show, divList){
	divList.forEach((div)=> div.style.display='none');
	div_to_show.style.display = 'block';
}

// create a table element
// accepts an array of objects that contains the data
// returns a table object
// raw_data -> an array of objects, each objects must conatain the same propeties
// properties_to_show -> an array that contains all the properties of the objects to be included in the table
// row_selection)funct -> a function to be called when a row is clicked
// table_class -> the html class of the table
// titles -> sn array that contains the titles of the table, must have the same size as properties_to_show
function createTable(raw_data, properties_to_show, row_selection_func, table_class, titles){
	if(raw_data.length==0) throw 'raw_data is empty';
	if(properties_to_show.length != titles.length) throw 'properties_to_show and titles has mismatching length' ;
	properties_to_show.forEach((property)=>{
		if(!raw_data[0].hasOwnProperty(property)) throw `${property} is not a property of the raw_data`;
	})
	let table = document.createElement('TABLE');
	table.className = table_class;

	// get the properties of the data
	let data_properties = Object.keys(raw_data[0]);

	// add the head 
	let thead = table.insertRow(0);
	titles.forEach((title, i)=>{
		let cell = thead.insertCell(i);
		cell.textContent = title;
	});
	raw_data.forEach((data, i) => {
		let row = table.insertRow(i+1);
		row.id = i;
		row.onclick = row_selection_func;
		properties_to_show.forEach((data_property, j) => {
			let data_property_value = data[data_property];
			let cell = row.insertCell(j);
			cell.textContent = data_property_value;
		});
	});
	return table;
}

// convert raw timestamp into a more huma readbable format
function convert_date(raw_date){
	const year_str = raw_date.substr(0, 4);
	const month_str = raw_date.substr(5, 2);
	const day_str = raw_date.substr(8, 2);

	return `${months[parseInt(month_str)]} ${day_str}, ${year_str}`
}

function convert_time(raw_time){
	let hour = parseInt(raw_time.substr(0, 2));
	let timestamp = 'AM';
	if(hour > 12){
		timestamp = 'PM';
		hour -= 12;
	}

	return `${hour}${raw_time.slice(2)} ${timestamp}`;
}

function processDateStr(date_str){
	const date = convert_date(date_str.slice(0, 10));
	const time = convert_time(date_str.slice(11, 19));

	return `${date} ${time}`;
}