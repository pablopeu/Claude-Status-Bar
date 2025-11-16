# Claude Code Status Bar

Barra de estado personalizada para Claude Code que muestra el uso de contexto en tiempo real y el próximo tiempo de reset.

## 📊 Características

- **Barra de progreso visual**: Muestra el uso de contexto con caracteres Unicode
- **Porcentaje de uso**: Indica el porcentaje del contexto utilizado
- **Tiempo de reset**: Muestra cuándo se resetea el límite de la sesión
- **Autosizeable**: Se ajusta automáticamente al ancho de la terminal
- **Detección automática del modelo**: Soporta Sonnet 4.5 (1M tokens) y otros modelos (200K tokens)
- **Detección del plan**: Muestra el plan de Claude Code si no hay datos de sesión disponibles

## 🎨 Formato de salida

```
[████████████░░░░░░░░] 45% Reset: Today 15:00
```

- **Barra de progreso**: Indica visualmente el total usado
- **Porcentaje**: Contexto usado expresado en %
- **Reset**: Hora en que se resetea la sesión

## 📦 Instalación

### 1. Copiar el script

Copia el archivo `usage_bar.py` a tu directorio de scripts de Claude Code:

```bash
# Crear directorio si no existe
mkdir -p ~/.claude-code/scripts

# Copiar el script
cp usage_bar.py ~/.claude-code/scripts/

# Dar permisos de ejecución
chmod +x ~/.claude-code/scripts/usage_bar.py
```

### 2. Configurar Claude Code

Edita tu archivo de configuración de Claude Code en `~/.claude/settings.json` y agrega:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude-code/scripts/usage_bar.py",
    "padding": 0
  }
}
```

### 3. Reiniciar Claude Code

Cierra y vuelve a abrir Claude Code para que los cambios surtan efecto.

## 🧪 Probar el script

Puedes probar el script manualmente con datos de ejemplo:

```bash
echo '{"current_tokens": 450000, "expected_total_tokens": 500000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 ~/.claude-code/scripts/usage_bar.py
```

Deberías ver una salida similar a:
```
[████████████████████░░░░░░░░░] 45% Reset: Today 15:00
```

## 🔧 Personalización

### Cambiar el formato de reset

Edita la función `calculate_next_reset()` en `usage_bar.py`:

```python
def calculate_next_reset():
    # Modifica la lógica de cálculo aquí
    # Por defecto usa bloques de 5 horas
    ...
```

### Cambiar caracteres de la barra

Edita la función `create_progress_bar()`:

```python
def create_progress_bar(percentage, width):
    filled = int(percentage * width / 100)
    empty = width - filled
    return "▰" * filled + "▱" * empty  # Cambia los caracteres aquí
```

### Ajustar límites de contexto

Edita la función `get_context_limit()`:

```python
def get_context_limit(model_info):
    # Agrega más modelos aquí
    if 'tu-modelo' in model_id:
        return 2_000_000  # 2M tokens
    ...
```

## 📖 Cómo funciona

1. Claude Code pasa datos de la sesión actual como JSON via stdin
2. El script lee el JSON y extrae:
   - `current_tokens`: Tokens usados actualmente
   - `expected_total_tokens`: Total esperado de tokens
   - `model`: Información del modelo
3. Calcula el porcentaje de uso según el límite del modelo
4. Determina el próximo tiempo de reset (bloques de 5 horas)
5. Crea una barra de progreso que se ajusta al ancho de la terminal
6. Retorna una línea formateada que Claude Code muestra en el status bar

## 🐛 Solución de problemas

### El status bar no aparece

1. Verifica que el archivo esté en la ubicación correcta: `~/.claude-code/scripts/usage_bar.py`
2. Asegúrate de que tenga permisos de ejecución: `chmod +x ~/.claude-code/scripts/usage_bar.py`
3. Verifica que la configuración en `~/.claude/settings.json` sea correcta
4. Revisa que Python 3 esté instalado: `python3 --version`

### Muestra "Claude Code (Error: ...)"

El script no puede leer los datos de stdin. Verifica que:
- Claude Code esté pasando el JSON correctamente
- El formato del JSON sea válido
- No haya problemas de permisos

### El porcentaje no es correcto

Claude Code tiene diferentes límites según el modelo:
- **Sonnet 4.5**: 1,000,000 tokens
- **Otros modelos**: 200,000 tokens

El script detecta automáticamente el modelo y ajusta el límite.

## 📝 Licencia

Este proyecto es de código abierto. Siéntete libre de modificarlo según tus necesidades.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras un bug o tienes una sugerencia, abre un issue o pull request.
