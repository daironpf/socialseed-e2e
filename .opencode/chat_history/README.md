# Chat History - Contexto Persistente para OpenCode

Este directorio almacena resúmenes de conversaciones importantes con OpenCode para mantener contexto entre sesiones.

## ⚠️ IMPORTANTE - Workaround para @context

El subagente `@context` tiene una **limitación técnica** donde no ejecuta las herramientas de lectura de archivos. Como solución alternativa, usamos un script de Python:

### Cargar Contexto con Script (RECOMENDADO)

```bash
# Desde la raíz del proyecto:
python3 .opencode/load_context.py

# O si lo hiciste ejecutable:
./.opencode/load_context.py
```

Este script lee automáticamente:
- `AGENTS.md` - Guía general del proyecto
- `.opencode/chat_history/consolidated_context.md` - Historial completo de sesiones

### Alternativa: @context (Puede no funcionar)

Si quieres intentar el subagente original:
```
@context
```
**Nota:** Puede reportar "No hay conversaciones previas" aunque existan archivos, debido a la limitación técnica mencionada.

---

## Archivos de Contexto

- **consolidated_context.md** - Resumen consolidado de TODAS las sesiones (usado por el script)
- **YYYYMMDD_*.md** - Archivos individuales de cada sesión
- **template.md** - Plantilla para nuevas entradas
- **README.md** - Este archivo

---

## Cómo usar este sistema

### Al iniciar una nueva sesión de OpenCode:

1. **Ejecuta el script de contexto:**
   ```bash
   python3 .opencode/load_context.py
   ```

2. **Lee `AGENTS.md`** en la raíz para información general del proyecto

3. **Revisa `consolidated_context.md`** para ver el historial completo

### Para guardar una conversación importante:

1. **Crea un archivo individual:**
   - Ubicación: `.opencode/chat_history/YYYYMMDD_descripcion_breve.md`
   - Ejemplo: `20250131_configuracion_cli.md`
   - Usa `template.md` como guía de formato

2. **Actualiza el archivo consolidado:**
   - Agrega un resumen de la nueva sesión en `consolidated_context.md`
   - Actualiza el contador "Total de sesiones"
   - Actualiza la fecha de "Última actualización"

### Formato de las entradas:

```markdown
# Título de la conversación
**Fecha:** YYYY-MM-DD
**Tema:** Breve descripción
**Estado:** [completado|en_progreso|pendiente]

## Resumen
Descripción de lo que se discutió/decidió

## Decisiones Importantes
- Decisión 1
- Decisión 2

## Código Generado/Modificado
- Archivo: `ruta/al/archivo.py`
  - Cambio: Descripción del cambio

## Próximos Pasos
1. Paso pendiente 1
2. Paso pendiente 2

## Notas
Cualquier información adicional relevante
```

---

## Tips

1. **Sé conciso:** Los resúmenes deben ser rápidos de leer
2. **Enfócate en decisiones:** Qué se decidió y por qué
3. **Menciona archivos clave:** Rutas de archivos modificados
4. **Estado actual:** Indica si hay tareas pendientes
5. **Mantén sincronizado:** Siempre actualiza `consolidated_context.md` después de crear un archivo individual
6. **Usa el script:** El script `load_context.py` es más confiable que `@context`

---

**Nota:** Este sistema es manual por diseño. El usuario debe indicar explícitamente cuando guardar un resumen. Esto evita que se guarden conversaciones irrelevantes o parciales.

Para guardar manualmente:
1. Crear archivo individual en `.opencode/chat_history/YYYYMMDD_descripcion.md`
2. Seguir el formato de `template.md`
3. Actualizar `consolidated_context.md` agregando la sesión al timeline
