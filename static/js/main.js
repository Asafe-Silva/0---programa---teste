document.querySelectorAll('.satisfacao').forEach(btn => {
    btn.addEventListener('click', async () => {
        const grau = btn.dataset.grau;
        btn.disabled = true;

        const response = await fetch('/registrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grau })
        });

        const data = await response.json();
        const feedback = document.getElementById('feedback');
        feedback.textContent = data.mensagem;
        feedback.classList.remove('hidden');

        setTimeout(() => {
            feedback.classList.add('hidden');
        }, 2000);
    });
});
