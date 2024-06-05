document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('question-form');
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();

        }
    });
});