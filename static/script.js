document.getElementById('draw-button').addEventListener('click', async () => {
    const res = await fetch('/draw', {method: 'POST'});
    const data = await res.json();
    const num = data.number;
    if (num === null) return;
    document.getElementById('number-display').textContent = num;
    const span = document.querySelector(`span[data-num="${num}"]`);
    if (span) span.classList.add('drawn');
});
