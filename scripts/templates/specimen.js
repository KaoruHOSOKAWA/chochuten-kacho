const sizeControl = document.querySelector('#sample-size');
const sizeOutput = document.querySelector('#sample-size-value');
function updateSampleSize() {
  const size = `${sizeControl.value}px`;
  document.documentElement.style.setProperty('--sample-size', size);
  sizeOutput.value = size;
}
sizeControl.addEventListener('input', updateSampleSize);
updateSampleSize();
