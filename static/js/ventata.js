const openPopupButton = document.getElementById('openPopup');
const popup = document.getElementById('popup');
const confirmButton = document.getElementById('confirmButton');
const cancelButton = document.getElementById('cancelButton');

// Abrir ventana emergente
openPopupButton.addEventListener('click', () => {
  popup.style.display = 'flex';
});

// Cerrar ventana emergente al hacer clic en "Cancelar"
cancelButton.addEventListener('click', () => {
  popup.style.display = 'none';
});

// Simplemente para ejemplo, aquí se puede agregar más lógica
confirmButton.addEventListener('click', () => {
  alert('Pedido confirmado');
  popup.style.display = 'none';
});