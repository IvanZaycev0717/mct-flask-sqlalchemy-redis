document.querySelectorAll('.article-card img').forEach(image =>{
    image.onclick = () => {
        document.querySelector('.popup-image').style.display = 'block';
        document.querySelector('.popup-image img').src = image.getAttribute('src');
    }
});
const popupImage = document.querySelector('.popup-image');
if (popupImage) {
    popupImage.onclick = () => {
        popupImage.style.display = 'none';
    };
};
