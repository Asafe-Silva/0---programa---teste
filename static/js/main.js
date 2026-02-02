document.querySelectorAll('.satisfacao').forEach(btn => {
    // preparar container para check transient
    const check = document.createElement('span');
    check.className = 'btn-check';
    check.textContent = '✓';
    btn.appendChild(check);

    btn.addEventListener('click', async (ev) => {
        const grau = btn.dataset.grau;
        btn.disabled = true;
        // ripple
        createRipple(btn, ev);

        // iniciar animação apropriada (retorna Promise que resolve quando a animação termina)
        let animPromise;
        if (grau === 'Muito satisfeito') animPromise = animateMuito(btn);
        else if (grau === 'Satisfeito') animPromise = animateSatisfeito(btn);
        else animPromise = animateInsatisfeito(btn);

        // enviar registro em paralelo
        let fetchMsg = null;
        try {
            const response = await fetch('/registrar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grau })
            });
            const data = await response.json();
            fetchMsg = data.mensagem;
        } catch (err) {
            console.error(err);
            fetchMsg = 'Erro ao enviar feedback.';
        }

        // mostrar mensagem assim que disponível
        if (fetchMsg) {
            const feedback = document.getElementById('feedback');
            feedback.textContent = fetchMsg;
            feedback.classList.remove('hidden');
        }

        // mostrar check momentâneo
        check.classList.add('show');
        setTimeout(() => check.classList.remove('show'), 900);

        // aguardar término da animação antes de reabilitar
        const duration = await animPromise;
        setTimeout(() => {
            const feedback = document.getElementById('feedback');
            feedback.classList.add('hidden');
            btn.disabled = false;
        }, 0);
    });
});

// animação: Muito satisfeito — quica/pula pela tela e volta
function animateMuito(btn) {
    return new Promise(resolve => {
        const rect = btn.getBoundingClientRect();
        const orig = { left: btn.style.left, top: btn.style.top, position: btn.style.position, zIndex: btn.style.zIndex, width: btn.style.width, height: btn.style.height };
        // fixar no lugar para animar com transform
        btn.style.position = 'fixed';
        btn.style.left = rect.left + 'px';
        btn.style.top = rect.top + 'px';
        btn.style.width = rect.width + 'px';
        btn.style.height = rect.height + 'px';
        btn.style.margin = '0';
        btn.style.zIndex = 9999;
        btn.classList.add('bounce-around');

        // duração da animação em CSS: 2200ms
        const dur = 2200;
        setTimeout(() => {
            btn.classList.remove('bounce-around');
            // restaurar estilos
            btn.style.position = orig.position || '';
            btn.style.left = orig.left || '';
            btn.style.top = orig.top || '';
            btn.style.width = orig.width || '';
            btn.style.height = orig.height || '';
            btn.style.zIndex = orig.zIndex || '';
            resolve(dur);
        }, dur + 30);
    });
}

// animação: Satisfeito — cresce e sorri
function animateSatisfeito(btn) {
    return new Promise(resolve => {
        const rect = btn.getBoundingClientRect();
        const orig = { left: btn.style.left, top: btn.style.top, position: btn.style.position, zIndex: btn.style.zIndex, width: btn.style.width, height: btn.style.height, inner: btn.innerHTML };
        btn.style.position = 'fixed';
        btn.style.left = rect.left + 'px';
        btn.style.top = rect.top + 'px';
        btn.style.width = rect.width + 'px';
        btn.style.height = rect.height + 'px';
        btn.style.margin = '0';
        btn.style.zIndex = 9999;
        // trocar emoji para sorriso maior durante animação
        const emoji = btn.querySelector('.emoji');
        const oldEmoji = emoji ? emoji.textContent : '';
        if (emoji) emoji.textContent = '😄';
        btn.classList.add('satisfeito-pop');

        const dur = 1800;
        setTimeout(() => {
            btn.classList.remove('satisfeito-pop');
            if (emoji) emoji.textContent = oldEmoji;
            btn.style.position = orig.position || '';
            btn.style.left = orig.left || '';
            btn.style.top = orig.top || '';
            btn.style.width = orig.width || '';
            btn.style.height = orig.height || '';
            btn.style.zIndex = orig.zIndex || '';
            resolve(dur);
        }, dur + 30);
    });
}

// animação: Insatisfeito — vai para o canto e chora
function animateInsatisfeito(btn) {
    return new Promise(resolve => {
        const rect = btn.getBoundingClientRect();
        const orig = { left: btn.style.left, top: btn.style.top, position: btn.style.position, zIndex: btn.style.zIndex, width: btn.style.width, height: btn.style.height };
        btn.style.position = 'fixed';
        btn.style.left = rect.left + 'px';
        btn.style.top = rect.top + 'px';
        btn.style.width = rect.width + 'px';
        btn.style.height = rect.height + 'px';
        btn.style.margin = '0';
        btn.style.zIndex = 9999;
        btn.classList.add('insatisfeito-run');

        // criar lágrimas (2) a partir da posição do botão
        const eyeLeft = rect.left + rect.width * 0.22;
        const eyeRight = rect.left + rect.width * 0.5;
        const eyeTop = rect.top + rect.height * 0.25;
        const tear1 = document.createElement('div');
        const tear2 = document.createElement('div');
        tear1.className = 'tear';
        tear2.className = 'tear';
        document.body.appendChild(tear1);
        document.body.appendChild(tear2);
        tear1.style.left = (eyeLeft) + 'px';
        tear1.style.top = (eyeTop) + 'px';
        tear2.style.left = (eyeRight) + 'px';
        tear2.style.top = (eyeTop + 6) + 'px';

        const dur = 2600;
        // remover lágrimas e restaurar depois
        setTimeout(() => {
            tear1.remove();
            tear2.remove();
            btn.classList.remove('insatisfeito-run');
            btn.style.position = orig.position || '';
            btn.style.left = orig.left || '';
            btn.style.top = orig.top || '';
            btn.style.width = orig.width || '';
            btn.style.height = orig.height || '';
            btn.style.zIndex = orig.zIndex || '';
            resolve(dur);
        }, dur + 50);
    });
}

function createRipple(element, ev) {
    const rect = element.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    // cor baseada no accent com opacidade
    ripple.style.background = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#ff4d4d';
    ripple.style.left = (x - 10) + 'px';
    ripple.style.top = (y - 10) + 'px';
    ripple.style.width = ripple.style.height = '20px';
    element.appendChild(ripple);
    setTimeout(() => { ripple.remove(); }, 700);
}

// Tema: carregar preferência e controlar toggle
const themeToggle = document.getElementById('themeToggle');
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    if (theme === 'light') themeToggle.textContent = '☀️'; else themeToggle.textContent = '🌙';
    localStorage.setItem('theme', theme);
}

const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);

themeToggle.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(cur === 'dark' ? 'light' : 'dark');
});

// Admin modal logic
const adminBtn = document.getElementById('adminBtn');
const adminModal = document.getElementById('adminModal');
const closeModal = document.getElementById('closeModal');
const adminLoginBtn = document.getElementById('adminLoginBtn');

adminBtn.addEventListener('click', () => {
    adminModal.classList.remove('hidden');
});
closeModal.addEventListener('click', () => {
    adminModal.classList.add('hidden');
});

adminLoginBtn.addEventListener('click', async () => {
    const username = document.getElementById('adminUser').value.trim();
    const senha = document.getElementById('adminPass').value.trim();
    const msg = document.getElementById('adminMsg');
    msg.textContent = '';
    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, senha })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            // redireciona para painel admin
            window.location.href = '/admin';
        } else {
            msg.textContent = data.mensagem || 'Erro no login';
        }
    } catch (e) {
        msg.textContent = 'Erro ao conectar ao servidor.';
    }
});
