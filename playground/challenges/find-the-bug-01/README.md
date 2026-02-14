# 🏆 Desafío 1: Encuentra el Bug

## 🎯 Objetivo

Encuentra **5 bugs ocultos** en el servicio de autenticación usando SocialSeed E2E.

## 📋 Reglas

1. No mires `BUGS.md` todavía (¡eso sería hacer trampa!)
2. Escribe tests que fallen para cada bug que encuentres
3. Documenta el comportamiento esperado vs actual
4. Categoriza cada bug (Seguridad/Funcional/Performance)

## 🚀 Inicio Rápido

```bash
# 1. Iniciar el servicio
cd ../broken-apps/auth-service-broken
python app.py

# 2. En otra terminal, inicializar tu proyecto de tests
mkdir my-challenge
cd my-challenge
e2e init

# 3. Configurar e2e.conf
# services:
#   auth-service:
#     name: auth-service
#     base_url: http://localhost:5001
#     health_endpoint: /health

# 4. Crear tests y encontrar bugs!
```

## 🐛 Pistas

### Pista 1: Seguridad
> "No todas las contraseñas están escondidas donde deberían estar"

### Pista 2: Validación
> "El sistema acepta cualquier cosa que parezca un token"

### Pista 3: Tiempo
> "Algunas cosas deberían expirar, pero no lo hacen"

### Pista 4: Privilegios
> "No todos los usuarios deberían ver todo"

### Pista 5: Información
> "El sistema revela demasiado cuando falla"

## ✅ Checklist

- [ ] Bug #1 encontrado y test escrito
- [ ] Bug #2 encontrado y test escrito
- [ ] Bug #3 encontrado y test escrito
- [ ] Bug #4 encontrado y test escrito
- [ ] Bug #5 encontrado y test escrito

## 🎁 Recompensa

Después de encontrar 5 bugs, compara tu lista con `BUGS.md`:

- ¿Encontraste bugs críticos de seguridad?
- ¿Descubriste bugs que no están documentados?
- ¿Cuántos de los 20 bugs totales pudiste identificar?

## 📝 Formato de Respuesta

Crea un archivo `FINDINGS.md`:

```markdown
# Mis Descubrimientos

## Bug 1: [Nombre descriptivo]
- **Categoría**: Seguridad/Funcional/Performance
- **Descripción**: Qué hace mal
- **Impacto**: Qué puede pasar si no se corrige
- **Test que lo detecta**: Cómo lo encontraste

## Bug 2: ...
```

## 🆘 Necesitas Ayuda?

- Revisa el [Tutorial 1](../tutorials/01-getting-started/) si no sabes por dónde empezar
- Lee la documentación de [Auth Service Broken](../broken-apps/auth-service-broken/BUGS.md) después de intentarlo
- Pregunta en [GitHub Discussions](https://github.com/daironpf/socialseed-e2e/discussions)

## ⏱️ Tiempo Estimado

- **Principiante**: 45-60 minutos
- **Intermedio**: 30-45 minutos
- **Avanzado**: 15-30 minutos

## 🏅 Logros

- 🥉 **Bronce**: Encontrar 3 bugs
- 🥈 **Plata**: Encontrar 5 bugs
- 🥇 **Oro**: Encontrar 8+ bugs
- 💎 **Diamante**: Encontrar 10+ bugs + escribir correcciones

---

**¡Buena suerte, detective!** 🕵️‍♂️
