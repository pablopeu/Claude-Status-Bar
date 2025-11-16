# Claude Code Status Bar

Barra de estado personalizada para Claude Code que muestra el uso de contexto en tiempo real y el próximo tiempo de reset.

![Status Bar Example](https://img.shields.io/badge/Status-[████████████░░░░░░░░]%2045%25%20Reset:%20Today%2015:00-green)

## 📊 Características

- ⚡ **Barra de progreso visual**: Muestra el uso de contexto con caracteres Unicode
- 📊 **Porcentaje de uso**: Indica el porcentaje del contexto utilizado
- ⏰ **Tiempo de reset**: Muestra cuándo se resetea el límite de la sesión
- 📏 **Autosizeable**: Se ajusta automáticamente al ancho de la terminal
- 🤖 **Detección automática del modelo**: Soporta Sonnet 4.5 (1M tokens) y otros modelos (200K tokens)
- 🎯 **Detección del plan**: Muestra el plan de Claude Code si no hay datos de sesión disponibles
- 🔄 **Actualización en tiempo real**: Se actualiza automáticamente con cada interacción
- 🐍 **Solo Python estándar**: No requiere dependencias externas

## 🎨 Formato de salida

```
[████████████░░░░░░░░] 45% Reset: Today 15:00
```

**Elementos:**
- `[████████████░░░░░░░░]` → Barra de progreso visual (se ajusta al ancho de la terminal)
- `45%` → Porcentaje del contexto utilizado
- `Reset: Today 15:00` → Próximo reset del límite de uso

## 📋 Requisitos previos

- **Claude Code** instalado y configurado
- **Python 3.6+** (ya viene instalado en la mayoría de sistemas Linux/macOS)
- Sistema operativo: Linux, macOS, o Windows (con WSL/Git Bash)

### Verificar Python

```bash
python3 --version
```

Si no está instalado:

**Debian/Ubuntu:**
```bash
sudo apt update && sudo apt install python3 -y
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 -y
```

**macOS:**
```bash
brew install python3
```

## 🚀 Instalación rápida

### Opción 1: Instalación automática (recomendada)

```bash
# Descargar el script
curl -O https://raw.githubusercontent.com/pablopeu/Claude-Status-Bar/main/usage_bar.py

# Crear directorio y copiar
mkdir -p ~/.claude-code/scripts
cp usage_bar.py ~/.claude-code/scripts/
chmod +x ~/.claude-code/scripts/usage_bar.py

# Probar que funciona
echo '{"current_tokens": 450000, "expected_total_tokens": 500000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 ~/.claude-code/scripts/usage_bar.py
```

Si ves la barra de progreso, ¡funciona! Continúa con la configuración de Claude Code.

### Opción 2: Clonar el repositorio

```bash
git clone https://github.com/pablopeu/Claude-Status-Bar.git
cd Claude-Status-Bar
mkdir -p ~/.claude-code/scripts
cp usage_bar.py ~/.claude-code/scripts/
chmod +x ~/.claude-code/scripts/usage_bar.py
```

## ⚙️ Configuración de Claude Code

### Paso 1: Editar el archivo de configuración

Abre el archivo de configuración de Claude Code:

```bash
# Opción 1: Con nano (más fácil para principiantes)
nano ~/.claude/settings.json

# Opción 2: Con vim
vim ~/.claude/settings.json

# Opción 3: Con tu editor favorito
code ~/.claude/settings.json  # VS Code
gedit ~/.claude/settings.json  # GNOME
```

### Paso 2: Agregar la configuración del status bar

**Si el archivo está vacío o no existe**, copia y pega esto:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude-code/scripts/usage_bar.py",
    "padding": 0
  }
}
```

**Si ya tienes otras configuraciones**, agrega solo la parte de `statusLine`:

```json
{
  "otherConfig": "...",
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude-code/scripts/usage_bar.py",
    "padding": 0
  }
}
```

**Guardar el archivo:**
- Con nano: `Ctrl+O`, Enter, luego `Ctrl+X`
- Con vim: `Esc`, luego `:wq`, Enter

### Paso 3: Reiniciar Claude Code

```bash
# Cierra completamente Claude Code (no solo la ventana)
# Luego vuelve a abrirlo
claude-code
```

### Paso 4: Verificar que funciona

Al abrir Claude Code, deberías ver la barra de estado en la parte inferior de la terminal:

```
[████████████░░░░░░░░] 45% Reset: Today 15:00
```

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

### ❌ El status bar no aparece

**Diagnóstico paso a paso:**

1. **Verificar ubicación del script:**
   ```bash
   ls -la ~/.claude-code/scripts/usage_bar.py
   ```
   Debería mostrar el archivo con permisos de ejecución (`-rwxr-xr-x`)

2. **Verificar permisos:**
   ```bash
   chmod +x ~/.claude-code/scripts/usage_bar.py
   ```

3. **Probar el script manualmente:**
   ```bash
   echo '{"current_tokens": 450000, "expected_total_tokens": 500000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 ~/.claude-code/scripts/usage_bar.py
   ```
   Si no muestra nada, revisa los errores de Python.

4. **Verificar la configuración:**
   ```bash
   cat ~/.claude/settings.json
   ```
   Asegúrate de que el JSON sea válido (puedes usar `python3 -m json.tool ~/.claude/settings.json`)

5. **Verificar Python 3:**
   ```bash
   python3 --version
   which python3
   ```

6. **Ver logs de Claude Code:**
   Cuando abras Claude Code, revisa si hay mensajes de error relacionados con el status bar.

### ⚠️ Muestra "Claude Code (Error: ...)"

**Causa:** El script no puede leer los datos de stdin.

**Soluciones:**

1. **Verificar formato JSON:**
   El error suele mostrar los primeros 20 caracteres del problema.
   - `Error: Expecting property n` → JSON inválido
   - `Error: No module named` → Falta Python o un módulo

2. **Probar directamente:**
   ```bash
   python3 ~/.claude-code/scripts/usage_bar.py
   ```
   Presiona `Ctrl+D` (EOF) para ver si hay errores de Python.

3. **Reinstalar el script:**
   ```bash
   # Descargar versión fresca
   curl -O https://raw.githubusercontent.com/pablopeu/Claude-Status-Bar/main/usage_bar.py
   cp usage_bar.py ~/.claude-code/scripts/
   chmod +x ~/.claude-code/scripts/usage_bar.py
   ```

### 📊 El porcentaje parece incorrecto

**Explicación:** Claude Code tiene diferentes límites según el modelo:

| Modelo | Límite de contexto | Detección |
|--------|-------------------|-----------|
| **Claude Sonnet 4.5** | 1,000,000 tokens (1M) | `sonnet-4-5`, `claude-sonnet-4-5` |
| **Claude Sonnet 3.5** | 200,000 tokens (200K) | `sonnet-3-5`, `claude-3-5-sonnet` |
| **Claude Opus** | 200,000 tokens (200K) | `opus` |
| **Claude Haiku** | 200,000 tokens (200K) | `haiku` |

El script detecta automáticamente el modelo del JSON que Claude Code pasa.

**Verificar qué modelo detecta:**
```bash
# Crea un script de prueba
cat > test_model.py << 'EOF'
import sys
sys.path.insert(0, '/home/tu-usuario/.claude-code/scripts')
from usage_bar import get_context_limit

models = [
    {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"},
    {"id": "claude-3-5-sonnet", "display_name": "Claude 3.5 Sonnet"},
    {"id": "claude-opus", "display_name": "Claude Opus"},
]

for model in models:
    limit = get_context_limit(model)
    print(f"{model['display_name']}: {limit:,} tokens")
EOF

python3 test_model.py
```

### 🔄 El tiempo de reset no coincide

**Sistema de reset de Claude Code:**
Los límites se resetean cada **5 horas** en bloques:
- 00:00 - 05:00
- 05:00 - 10:00
- 10:00 - 15:00
- 15:00 - 20:00
- 20:00 - 01:00 (día siguiente)

**Ejemplo:**
Si son las 14:30, el próximo reset es a las 15:00 (mismo día).
Si son las 22:00, el próximo reset es a las 00:00 (día siguiente).

### 🖥️ Problemas en Windows

Si usas Windows, asegúrate de:

1. **Usar WSL (Windows Subsystem for Linux)** o **Git Bash**
2. **Verificar rutas:**
   ```bash
   # En WSL, las rutas son Linux-style
   ~/.claude-code/scripts/usage_bar.py
   ```
3. **Usar Python de WSL:**
   ```bash
   which python3
   # Debería mostrar: /usr/bin/python3 (no una ruta de Windows)
   ```

## ❓ Preguntas frecuentes (FAQ)

### ¿Funciona con Claude Code en la web?
Sí, si estás usando Claude Code en el navegador, el status bar también funciona.

### ¿Necesito instalar librerías adicionales?
No, el script usa solo la librería estándar de Python (json, sys, shutil, datetime).

### ¿Puedo cambiar los colores de la barra?
Los caracteres Unicode (`█` y `░`) toman el color de tu terminal. Puedes personalizarlos editando la función `create_progress_bar()`:
```python
return "▰" * filled + "▱" * empty  # Caracteres alternativos
```

### ¿Cómo actualizo el script a una nueva versión?
```bash
cd Claude-Status-Bar
git pull origin main
cp usage_bar.py ~/.claude-code/scripts/
```

### ¿Funciona con otros modelos de IA (OpenAI, Gemini)?
Este script está diseñado específicamente para Claude Code. Para otros modelos necesitarías adaptar las funciones de detección.

### ¿Puedo contribuir al proyecto?
¡Sí! Las contribuciones son bienvenidas. Por favor abre un issue o pull request en GitHub.

## 📝 Licencia

Este proyecto es de código abierto. Siéntete libre de modificarlo según tus necesidades.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras un bug o tienes una sugerencia, abre un issue o pull request.
