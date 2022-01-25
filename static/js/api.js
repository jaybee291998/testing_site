// get the data from the server
async function get_data(domain){
	const res = await fetch(domain);
	const data = await res.json();
	return data;
}

// post and put
async function post_update(domain, type, obj_data, csrftoken){
	const request = get_request_obj(type, domain, obj_data, csrftoken);
	const res = await fetch(request);
	const data = await res.json();
	return data;
}


// delete
async function del(domain, csrftoken){
	const request = get_request_obj('DELETE', domain, null, csrftoken);
	const response = await fetch(request);
	return response;
}

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
		    var cookie = cookies[i].trim();
		    if (cookie.substring(0, name.length + 1) === (name + '=')) {
		    	cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
		    	break;
		    }
		}
	}
	return cookieValue;
}
// get the request object
function get_request_obj(type, domain, data, csrftoken){
	const url = domain;
	const request = new Request(url, {
		method: type,
		body: JSON.stringify(data),
		headers: new Headers({
			'Content-Type': 'application/json',
			'X-CSRFToken': csrftoken
		})
	});

	return request;
}