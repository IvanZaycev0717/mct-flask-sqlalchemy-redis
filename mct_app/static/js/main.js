const toastContent = document.querySelector('.toast');

if (!localStorage.getItem('toastShown')) {
    const toast = new bootstrap.Toast(toastContent, { autohide: false }); // Отключаем автоматическое скрытие

    toast.show();

    setTimeout(function(){
        toast.hide();
    }, 15000);

    localStorage.setItem('toastShown', 'true');
}