# 🎮 SocialSeed E2E Interactive Playground

Bienvenido al playground interactivo de SocialSeed E2E - un espacio diseñado para aprender, practicar y dominar el framework a través de ejemplos prácticos.

## 📁 Estructura del Playground

```
playground/
├── broken-apps/          # Aplicaciones intencionalmente rotas
├── tutorials/            # Tutoriales paso a paso
├── videos/               # Demostraciones en video
└── challenges/           # Desafíos interactivos
```

## 🎯 Objetivos de Aprendizaje

1. **Comenzar rápidamente**: Aprende los conceptos básicos en 5 minutos
2. **Detectar bugs**: Identifica problemas comunes en APIs
3. **Generar tests con IA**: Usa la inteligencia artificial para crear tests
4. **Depurar fallos**: Aprende a diagnosticar y corregir errores
5. **Dominar el framework**: Conviértete en experto en SocialSeed E2E

## 🚀 Primeros Pasos

### Opción 1: Tutorial Guiado (Recomendado)
```bash
cd tutorials/01-getting-started
# Sigue las instrucciones en README.md
```

### Opción 2: Explorar Apps Rotas
```bash
cd broken-apps/auth-service-broken
# Lee BUGS.md para ver qué está roto
# Intenta encontrar los bugs tú mismo
```

### Opción 3: Aceptar un Desafío
```bash
cd challenges/find-the-bug-01
# Lee el desafío y intenta resolverlo
```

## 📚 Tutoriales Disponibles

### Tutorial 1: Primeros Pasos (15 min)
- Instalación y configuración
- Tu primer test E2E
- Conceptos básicos del framework

### Tutorial 2: Generación de Tests con IA (20 min)
- Configurar el AI Orchestrator
- Generar tests automáticamente
- Personalizar tests generados

### Tutorial 3: Depuración de Fallos (25 min)
- Análisis de errores comunes
- Uso del Interactive Doctor
- Corrección de tests fallidos

## 🐛 Aplicaciones Rotas

Cada aplicación tiene bugs intencionales documentados en su archivo `BUGS.md`:

### Auth Service Broken
- **Problemas**: JWT inválido, tokens expirados, validación incorrecta
- **Dificultad**: ⭐⭐ Fácil
- **Aprendizaje**: Autenticación y manejo de tokens

### Payment Service Broken
- **Problemas**: Race conditions, validación de montos, idempotencia
- **Dificultad**: ⭐⭐⭐ Medio
- **Aprendizaje**: Transacciones y concurrencia

### E-commerce Broken
- **Problemas**: Múltiples bugs en flujo completo de compra
- **Dificultad**: ⭐⭐⭐⭐ Difícil
- **Aprendizaje**: Flujos complejos end-to-end

## 🏆 Desafíos

### Desafío 1: Encuentra el Bug
- Encuentra 5 bugs ocultos en la API
- Dificultad: ⭐⭐⭐
- Tiempo estimado: 30 minutos

### Desafío 2: Arregla el Test
- Corrige tests que fallan por bugs sutiles
- Dificultad: ⭐⭐⭐⭐
- Tiempo estimado: 45 minutos

## 🎥 Videos Demostrativos

- **Quickstart Demo** (5 min): Configuración inicial y primer test
- **AI Autonomy Demo** (10 min): Tests generados completamente por IA
- **Debugging Demo** (8 min): Depuración con Interactive Doctor

## 💡 Consejos para Instructores

Si estás enseñando SocialSeed E2E a un equipo:

1. **Workshop de 1 hora**: Tutorial 1 + Auth Service Broken
2. **Workshop de 2 horas**: Tutorial 1-2 + 2 apps rotas
3. **Workshop de 4 horas**: Todo el contenido + desafíos

## 🤝 Contribuir al Playground

¿Tienes ideas para nuevas apps rotas o desafíos?

1. Crea una app con bugs realistas
2. Documenta los bugs en BUGS.md
3. Añade tests de ejemplo que fallen
4. Sigue la estructura existente

## 📖 Recursos Adicionales

- [Documentación Principal](../docs/)
- [Guía de Referencia](../docs/configuration-reference.md)
- [API Documentation](../docs/api.md)

## 🆘 Soporte

- GitHub Issues: [socialseed-e2e/issues](https://github.com/daironpf/socialseed-e2e/issues)
- Discussions: [GitHub Discussions](https://github.com/daironpf/socialseed-e2e/discussions)

---

**¡Diviértete aprendiendo!** 🚀

*"El mejor modo de predecir el futuro es crear tests para él"*
