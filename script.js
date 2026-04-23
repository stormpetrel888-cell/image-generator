const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');
const placeholderText = document.getElementById('placeholderText');
const clearButton = document.getElementById('clearButton');
const downloadButton = document.getElementById('downloadButton');

imageInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    previewImage.src = reader.result;
    previewImage.style.display = 'block';
    placeholderText.style.display = 'none';
    downloadButton.disabled = false;
    downloadButton.dataset.filename = file.name;
  };
  reader.readAsDataURL(file);
});

clearButton.addEventListener('click', () => {
  imageInput.value = '';
  previewImage.src = '';
  previewImage.style.display = 'none';
  placeholderText.style.display = 'block';
  downloadButton.disabled = true;
  delete downloadButton.dataset.filename;
});

downloadButton.addEventListener('click', () => {
  if (!previewImage.src) return;

  const link = document.createElement('a');
  link.href = previewImage.src;
  link.download = downloadButton.dataset.filename || 'downloaded-image';
  link.click();
});
