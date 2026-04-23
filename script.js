const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');
const placeholderText = document.getElementById('placeholderText');
const clearButton = document.getElementById('clearButton');

imageInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    previewImage.src = reader.result;
    previewImage.style.display = 'block';
    placeholderText.style.display = 'none';
  };
  reader.readAsDataURL(file);
});

clearButton.addEventListener('click', () => {
  imageInput.value = '';
  previewImage.src = '';
  previewImage.style.display = 'none';
  placeholderText.style.display = 'block';
});
