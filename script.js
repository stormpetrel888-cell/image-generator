const imageInput = document.getElementById('imageInput');
const previewImage = document.getElementById('previewImage');
const placeholderText = document.getElementById('placeholderText');
const clearButton = document.getElementById('clearButton');
const downloadButton = document.getElementById('downloadButton');
const grayscaleButton = document.getElementById('grayscaleButton');

let currentImageName = '';
let originalImageSrc = '';

imageInput.addEventListener('change', (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    originalImageSrc = reader.result;
    currentImageName = file.name;
    previewImage.src = originalImageSrc;
    previewImage.style.display = 'block';
    placeholderText.style.display = 'none';
    downloadButton.disabled = false;
    grayscaleButton.disabled = false;
  };
  reader.readAsDataURL(file);
});

clearButton.addEventListener('click', () => {
  imageInput.value = '';
  previewImage.src = '';
  previewImage.style.display = 'none';
  placeholderText.style.display = 'block';
  downloadButton.disabled = true;
  grayscaleButton.disabled = true;
  currentImageName = '';
  originalImageSrc = '';
});

grayscaleButton.addEventListener('click', () => {
  if (!previewImage.src) return;

  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    canvas.width = img.width;
    canvas.height = img.height;
    context.drawImage(img, 0, 0);

    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
      const red = data[i];
      const green = data[i + 1];
      const blue = data[i + 2];
      const gray = 0.299 * red + 0.587 * green + 0.114 * blue;

      data[i] = gray;
      data[i + 1] = gray;
      data[i + 2] = gray;
    }

    context.putImageData(imageData, 0, 0);
    previewImage.src = canvas.toDataURL('image/png');
  };
  img.src = previewImage.src;
});

downloadButton.addEventListener('click', () => {
  if (!previewImage.src) return;

  const link = document.createElement('a');
  link.href = previewImage.src;

  const dotIndex = currentImageName.lastIndexOf('.');
  const baseName = dotIndex > 0 ? currentImageName.slice(0, dotIndex) : currentImageName || 'image';
  link.download = `${baseName}-edited.png`;
  link.click();
});
