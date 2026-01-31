# Chat History - Contexto Persistente para OpenCode

Este directorio almacena resúmenes de conversaciones importantes con OpenCode para mantener contexto entre sesiones.

## Cómo usar este sistema

### Al iniciar una nueva sesión de OpenCode:

1. **Lee el archivo `AGENTS.md`** en la raíz del proyecto primero
2. **Revisa los archivos en `.opencode/chat_history/`** para entender el contexto previo
3. **Ejecuta `@context` o pregunta** "¿Cuál es el contexto actual del proyecto?"

### Para guardar una conversación importante:

Crea un archivo en `.opencode/chat_history/` con el formato:

```
YYYYMMDD_descripcion_breve.md
```

Ejemplo: `20250131_configuracion_cli.md`

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

## Archivos en este directorio

- **README.md** - Este archivo (instrucciones)
- **template.md** - Plantilla para nuevas entradas
- **2025*.md** - Entradas históricas ordenadas por fecha

## Tips

1. **Sé conciso:** Los resúmenes deben ser rápidos de leer
2. **Enfócate en decisiones:** Qué se decidió y por qué
3. **Menciona archivos clave:** Rutas de archivos modificados
4. **Estado actual:** Indica si hay tareas pendientes
5. **Borra lo obsoleto:** Elimina archivos de conversaciones muy antiguas

---

**Nota:** Este sistema es manual. OpenCode no escribe automáticamente aquí, 
debes indicarle explícitamente "Guarda un resumen de esta conversación en 
.opencode/chat_history/" cuando termines una sesión importante.
