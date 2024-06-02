var imgElement = document.querySelector('.image-thumbnail img');
var currentSrc = imgElement.getAttribute('src');
var newSrc = currentSrc.replace(/%5C/g, '\\');
imgElement.setAttribute('src', newSrc);