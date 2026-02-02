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
        // criar um clone para animar e esconder o original (mantém layout)
        const clone = btn.cloneNode(true);
        clone.style.position = 'fixed';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.width = rect.width + 'px';
        clone.style.height = rect.height + 'px';
        clone.style.margin = '0';
        clone.style.zIndex = 9999;
        clone.style.pointerEvents = 'none';
        document.body.appendChild(clone);
        // esconder original sem colapsar layout
        const oldVis = btn.style.visibility;
        btn.style.visibility = 'hidden';

        const margin = 12;
        const minX = margin;
        const maxX = Math.max(margin, window.innerWidth - rect.width - margin);
        const minY = margin;
        const maxY = Math.max(margin, window.innerHeight - rect.height - margin);

        const points = [
            { x: rect.left, y: rect.top, s: 1 },
            { x: Math.random() * (maxX - minX) + minX, y: Math.random() * (maxY - minY) + minY, s: 1.4 },
            { x: Math.random() * (maxX - minX) + minX, y: Math.random() * (maxY - minY) + minY, s: 1.25 },
            { x: rect.left, y: rect.top, s: 1 }
        ];

        const keyframes = points.map(p => ({ transform: `translate(${Math.round(p.x - rect.left)}px, ${Math.round(p.y - rect.top)}px) scale(${p.s})` }));
        const dur = 2200;
        const anim = clone.animate(keyframes, { duration: dur, easing: 'cubic-bezier(.25,.8,.25,1)', fill: 'forwards' });
        anim.onfinish = () => {
            clone.remove();
            btn.style.visibility = oldVis || '';
            resolve(dur);
        };
    });
}

// animação: Satisfeito — cresce e sorri
function animateSatisfeito(btn) {
    return new Promise(resolve => {
        const rect = btn.getBoundingClientRect();
        const clone = btn.cloneNode(true);
        clone.style.position = 'fixed';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.width = rect.width + 'px';
        clone.style.height = rect.height + 'px';
        clone.style.margin = '0';
        clone.style.zIndex = 9999;
        clone.style.pointerEvents = 'none';
        document.body.appendChild(clone);
        const oldVis = btn.style.visibility;
        btn.style.visibility = 'hidden';

        // alterar emoji no clone
        const emoji = clone.querySelector('.emoji');
        const oldEmoji = emoji ? emoji.textContent : '';
        if (emoji) emoji.textContent = '😄';

        clone.classList.add('satisfeito-pop');
        const dur = 1800;
        const anim = clone.animate([
            { transform: 'scale(1) translateY(0) rotate(0deg)' },
            { transform: 'scale(1.6) translateY(-18px) rotate(-6deg)' },
            { transform: 'scale(1.18) translateY(6px) rotate(6deg)' },
            { transform: 'scale(1) translateY(0) rotate(0deg)' }
        ], { duration: dur, easing: 'ease', fill: 'forwards' });

        anim.onfinish = () => {
            clone.remove();
            btn.style.visibility = oldVis || '';
            resolve(dur);
        };
    });
}

// animação: Insatisfeito — vai para o canto e chora
function animateInsatisfeito(btn) {
    return new Promise(resolve => {
        const rect = btn.getBoundingClientRect();
        const clone = btn.cloneNode(true);
        clone.style.position = 'fixed';
        clone.style.left = rect.left + 'px';
        clone.style.top = rect.top + 'px';
        clone.style.width = rect.width + 'px';
        clone.style.height = rect.height + 'px';
        clone.style.margin = '0';
        clone.style.zIndex = 9999;
        clone.style.pointerEvents = 'none';
        document.body.appendChild(clone);
        const oldVis = btn.style.visibility;
        btn.style.visibility = 'hidden';

        const margin = 12;
        const targetX = margin; // canto esquerdo
        const targetY = Math.max(margin, window.innerHeight - rect.height - margin);

        // animar clone usando transform para não modificar layout
        const deltaX = targetX - rect.left;
        const deltaY = targetY - rect.top;
        const dur = 2600;
        const anim = clone.animate([
            { transform: 'translate(0px,0px) scale(1)' },
            { transform: `translate(${deltaX}px, ${deltaY}px) scale(1.12)` },
            { transform: 'translate(0px,0px) scale(1)' }
        ], { duration: dur, easing: 'ease-in-out', fill: 'forwards' });

        // criar lágrimas e animá-las a partir do clone's coordinates
        const eyeLeft = rect.left + rect.width * 0.22;
        const eyeRight = rect.left + rect.width * 0.6;
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

        const endY1 = Math.max(20, window.innerHeight - (eyeTop) - 10);
        const endY2 = Math.max(20, window.innerHeight - (eyeTop + 6) - 10);

        tear1.animate([
            { transform: 'translateY(0px) rotate(0deg)', opacity: 0.95 },
            { transform: `translateY(${endY1}px) rotate(18deg)`, opacity: 0.2 }
        ], { duration: 1100, easing: 'linear', fill: 'forwards' });

        tear2.animate([
            { transform: 'translateY(0px) rotate(0deg)', opacity: 0.95 },
            { transform: `translateY(${endY2}px) rotate(22deg)`, opacity: 0.2 }
        ], { duration: 1200, easing: 'linear', fill: 'forwards' });

        anim.onfinish = () => {
            try { tear1.remove(); } catch (e) {}
            try { tear2.remove(); } catch (e) {}
            clone.remove();
            btn.style.visibility = oldVis || '';
            resolve(dur);
        };
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

// Admin modal logic (somente se existir o botão/modal na página)
const adminBtn = document.getElementById('adminBtn');
const adminModal = document.getElementById('adminModal');
const closeModal = document.getElementById('closeModal');
const adminLoginBtn = document.getElementById('adminLoginBtn');

if (adminBtn && adminModal) {
    adminBtn.addEventListener('click', () => {
        adminModal.classList.remove('hidden');
    });
}
if (closeModal && adminModal) {
    closeModal.addEventListener('click', () => {
        adminModal.classList.add('hidden');
    });
}
if (adminLoginBtn) {
    adminLoginBtn.addEventListener('click', async () => {
        const usernameEl = document.getElementById('adminUser');
        const senhaEl = document.getElementById('adminPass');
        const msg = document.getElementById('adminMsg');
        if (!usernameEl || !senhaEl || !msg) return;
        const username = usernameEl.value.trim();
        const senha = senhaEl.value.trim();
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
}

// botão inicio no topo (já presente no layout)
const inicioBtn = document.getElementById('inicioBtn');
if (inicioBtn) {
    inicioBtn.addEventListener('click', (e) => {
        // navega para a raiz
    });
}
