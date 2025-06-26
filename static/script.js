const drawButton = document.getElementById('draw-button');
const numberDisplay = document.getElementById('number-display');

drawButton.addEventListener('click', async () => {
    drawButton.disabled = true;

    // start shuffling numbers while fetching the next draw
    let shuffleInterval = setInterval(() => {
        const rand = Math.floor(Math.random() * 75) + 1;
        numberDisplay.textContent = rand;
    }, 75);

    const start = Date.now();
    const res = await fetch('/draw', {method: 'POST'});
    const data = await res.json();
    const num = data.number;
    if (num === null) {
        clearInterval(shuffleInterval);
        drawButton.disabled = false;
        return;
    }

    // ensure the shuffle lasts at least 1 second
    const delay = Math.max(1000 - (Date.now() - start), 0);
    setTimeout(() => {
        clearInterval(shuffleInterval);
        numberDisplay.textContent = num;
        const span = document.querySelector(`span[data-num="${num}"]`);
        if (span) span.classList.add('drawn');
        drawButton.disabled = false;
    }, delay);
});

document.getElementById('reset-button').addEventListener('click', async () => {
    await fetch('/reset', {method: 'POST'});
    document.getElementById('number-display').textContent = '--';
    document.querySelectorAll('#numbers .num').forEach(span => span.classList.remove('drawn'));
});
