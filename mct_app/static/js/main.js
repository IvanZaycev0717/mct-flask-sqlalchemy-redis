document.addEventListener('DOMContentLoaded', function() {
    var myModal = document.getElementById('myModal');

    var bootstrapModal = new bootstrap.Modal(myModal, {backdrop: true, keyboard: true});
    setTimeout(function() {
        bootstrapModal.show();
      }, 700);
  });