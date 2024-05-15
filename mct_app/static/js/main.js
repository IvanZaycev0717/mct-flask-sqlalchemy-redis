document.addEventListener('DOMContentLoaded', function() {
    var myModal = document.getElementById('myModal');
    var myInput = myModal.querySelector('input');
  
    myModal.addEventListener('shown.bs.modal', function () {
      myInput.focus();
    });
  
    var bootstrapModal = new bootstrap.Modal(myModal);
    setTimeout(function() {
        bootstrapModal.show();
      }, 700);
  });

const toastContent = document.querySelector('.toast');

if (!localStorage.getItem('toastShown')) {
    const toast = new bootstrap.Toast(toastContent, { autohide: false }); // Отключаем автоматическое скрытие

    toast.show();

    setTimeout(function(){
        toast.hide();
    }, 15000);

    localStorage.setItem('toastShown', 'true');
};
