function showDivBase(div_to_show, divList){
	divList.forEach((div)=> div.style.display='none');
	div_to_show.style.display = 'block';
}

// create a table element
// accepts an array of objects that contains the data
// returns a table object
function createTable(raw_data, row_selection_func, table_class, titles){
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
		data_properties.forEach((data_property, j) => {
			let data_property_value = data[data_property];
			let cell = row.insertCell(j);
			cell.textContent = data_property_value;
		});
	});
	return table;
}