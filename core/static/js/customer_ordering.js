const qtyInputs = document.querySelectorAll('.co-qty-input');
const totalQty = document.getElementById('total-qty');
const totalPrice = document.getElementById('total-price');

function updateTotals() {
  let totalItems = 0;
  let totalCost = 0;
  qtyInputs.forEach(input => {
    const qty = parseInt(input.value) || 0;
    const price = parseFloat(input.dataset.price);
    totalItems += qty;
    totalCost += qty * price;
  });
  totalQty.textContent = totalItems;
  totalPrice.textContent = totalCost.toFixed(2);
}

qtyInputs.forEach(input => {
  input.addEventListener('input', updateTotals);
});

updateTotals();
