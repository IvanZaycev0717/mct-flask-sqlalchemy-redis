var fragment = window.location.hash.substr(1);
var params = new URLSearchParams(fragment);

var token = params.get('access_token');
var session = params.get('session_secret_key');

var xhr = new XMLHttpRequest();
xhr.open('GET', '/ok-callback?access_token=' + token + '&session_secret_key=' + session, true);
xhr.onreadystatechange = function() {
  if (xhr.readyState === 4 && xhr.status === 200) {
    console.log(xhr.responseText);
  }
};
xhr.send();