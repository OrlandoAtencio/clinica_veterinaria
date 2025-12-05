// static/js/login.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        // Validación básica
        if (!email || !password) {
            alert('Por favor, complete todos los campos');
            return;
        }
        
        // Deshabilitar botón durante el proceso
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Iniciando sesión...';
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Login exitoso
                alert('¡Login exitoso! Redirigiendo...');
                window.location.href = data.redirect;
            } else {
                // Login fallido
                alert(data.message || 'Credenciales incorrectas');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
});