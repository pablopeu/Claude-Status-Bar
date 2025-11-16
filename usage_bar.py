#!/usr/bin/env python3
# ~/.claude-code/scripts/usage_bar.py
"""
Claude Code Status Bar - Muestra uso de contexto y tiempo de reset
Formato: [████████░░] 75% Reset: Sat 00:00
"""
import json
import sys
import shutil
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def get_terminal_width():
    """Obtiene el ancho actual de la terminal"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def get_web_usage_data():
    """
    Obtiene datos de uso directamente desde claude.ai/settings/usage
    Retorna: (percentage, reset_time_str) o (None, None) si falla
    """
    cache_file = Path.home() / ".claude-code" / "usage-cache.json"
    cache_duration = 60  # segundos

    # Verificar cache
    if cache_file.exists():
        try:
            cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if cache_age < cache_duration:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    return cache_data.get('percentage'), cache_data.get('reset_time')
        except:
            pass

    # Leer credenciales
    creds_file = Path.home() / ".claude" / ".credentials.json"
    if not creds_file.exists():
        return None, None

    try:
        with open(creds_file, 'r') as f:
            creds = json.load(f)
            token = creds.get('claudeAiOauth', {}).get('accessToken', '')

        if not token:
            return None, None

        # Intentar obtener datos con curl
        result = subprocess.run([
            'curl', '-s', '-L',
            'https://claude.ai/settings/usage',
            '-H', f'Cookie: sessionKey={token}',
            '-H', 'User-Agent: Mozilla/5.0'
        ], capture_output=True, text=True, timeout=5)

        html = result.stdout

        # Parsear HTML para extraer porcentaje y reset time
        # Buscar patrones como "69% used" y "Resets in 3 hr 27 min"
        percentage_match = re.search(r'(\d+)%\s*used', html, re.IGNORECASE)
        reset_match = re.search(r'Resets in (\d+)\s*hr\s*(\d+)\s*min', html, re.IGNORECASE)

        if percentage_match:
            percentage = int(percentage_match.group(1))

            # Calcular reset time
            reset_str = None
            if reset_match:
                hours = int(reset_match.group(1))
                minutes = int(reset_match.group(2))
                reset_time = datetime.now() + timedelta(hours=hours, minutes=minutes)

                # Formato: "Today 17:00" o "Tmrw 02:00"
                if reset_time.date() == datetime.now().date():
                    reset_str = f"Today {reset_time.strftime('%H:%M')}"
                elif reset_time.date() == (datetime.now() + timedelta(days=1)).date():
                    reset_str = f"Tmrw {reset_time.strftime('%H:%M')}"
                else:
                    reset_str = reset_time.strftime("%a %H:%M")

            # Guardar en cache
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump({
                        'percentage': percentage,
                        'reset_time': reset_str,
                        'timestamp': datetime.now().isoformat()
                    }, f)
            except:
                pass

            return percentage, reset_str

    except Exception as e:
        pass

    return None, None

def get_context_limit(model_info):
    """
    Determina el límite de contexto según el modelo
    - Sonnet 4.5: 1.7M tokens (límite de sesión para Claude Pro)
    - Otros modelos: 200K tokens
    """
    if not model_info:
        return 200_000

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    # Detectar Sonnet 4.5 (1.7M session limit para Claude Pro)
    # Nota: El context window es 1M, pero el límite de sesión es ~1.7M
    if 'sonnet-4-5' in model_id or 'sonnet 4.5' in model_name or 'claude-sonnet-4-5' in model_id:
        return 1_700_000

    # Por defecto 200K para otros modelos
    return 200_000

def get_plan_name(model_info):
    """
    Determina el nombre del plan según el modelo
    """
    if not model_info:
        return "Free"

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    if 'opus' in model_id or 'opus' in model_name:
        return "Pro"
    elif 'sonnet' in model_id or 'sonnet' in model_name:
        return "Pro"
    elif 'haiku' in model_id or 'haiku' in model_name:
        return "Free"

    return "Free"

def calculate_session_reset(session_id):
    """
    Calcula el reset de la sesión basado en el primer mensaje + 5 horas
    La sesión dura 5 horas desde el primer mensaje o hasta que se alcance el límite
    """
    # Buscar el archivo JSONL de la sesión
    possible_paths = [
        Path.home() / ".claude" / "projects",
        Path.home() / ".config" / "claude" / "projects"
    ]

    for base_path in possible_paths:
        if not base_path.exists():
            continue

        for jsonl_file in base_path.rglob("*.jsonl"):
            if session_id in jsonl_file.name:
                try:
                    # Leer líneas hasta encontrar el primer timestamp (inicio de sesión)
                    with open(jsonl_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if not line.strip():
                                continue

                            data = json.loads(line)

                            # Buscar timestamp en diferentes ubicaciones
                            timestamp = None
                            if 'timestamp' in data:
                                timestamp = data['timestamp']
                            elif 'created_at' in data:
                                timestamp = data['created_at']
                            elif 'message' in data and 'timestamp' in data['message']:
                                timestamp = data['message']['timestamp']

                            if timestamp:
                                # Parsear timestamp y calcular reset (inicio + 5 horas)
                                try:
                                    start_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    # Convertir a hora local si es necesario
                                    if start_time.tzinfo:
                                        start_time = start_time.astimezone()
                                    reset_time = start_time + timedelta(hours=5)
                                    return reset_time.strftime('%H:%M')
                                except:
                                    pass
                                # Salir después de encontrar el primer timestamp válido
                                break
                except:
                    pass

    # Fallback: si no se encuentra, retornar hora desconocida
    return "--:--"

def get_session_tokens(session_id):
    """
    Lee el archivo JSONL de la sesión y calcula los tokens totales
    Retorna: (input_tokens, output_tokens, cache_creation, cache_read)
    """
    # Buscar en las posibles ubicaciones de Claude
    possible_paths = [
        Path.home() / ".claude" / "projects",
        Path.home() / ".config" / "claude" / "projects"
    ]

    for base_path in possible_paths:
        if not base_path.exists():
            continue

        # Buscar el archivo JSONL de esta sesión
        for jsonl_file in base_path.rglob("*.jsonl"):
            if session_id in jsonl_file.name:
                return parse_jsonl_tokens(jsonl_file)

    return 0, 0, 0, 0

def parse_jsonl_tokens(jsonl_path):
    """
    Parsea un archivo JSONL y suma todos los tokens
    """
    total_input = 0
    total_output = 0
    total_cache_creation = 0
    total_cache_read = 0

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)

                # Extraer usage de diferentes ubicaciones posibles
                usage = data.get('usage', {})
                if not usage and 'message' in data:
                    usage = data['message'].get('usage', {})

                total_input += usage.get('input_tokens', 0)
                total_output += usage.get('output_tokens', 0)
                total_cache_creation += usage.get('cache_creation_input_tokens', 0)
                total_cache_read += usage.get('cache_read_input_tokens', 0)

    except Exception as e:
        # Si hay error leyendo el archivo, retornar ceros
        pass

    return total_input, total_output, total_cache_creation, total_cache_read

def get_color_code(percentage):
    """
    Retorna código de color ANSI según el porcentaje de uso
    Verde: 0-50%, Amarillo: 50-80%, Rojo: 80-100%
    """
    if percentage >= 80:
        return "\033[31m"  # Rojo (menos brillante para fondo negro)
    elif percentage >= 50:
        return "\033[33m"  # Amarillo (menos brillante para fondo negro)
    else:
        return "\033[32m"  # Verde (menos brillante para fondo negro)

def create_progress_bar(percentage, width):
    """Crea la barra de progreso con caracteres Unicode y colores"""
    filled = int(percentage * width / 100)
    empty = width - filled

    # Código de color según el porcentaje
    color = get_color_code(percentage)
    reset = "\033[0m"  # Reset color

    # Crear barra con color usando caracteres muy tenues
    # ░ (light shade) para relleno - muy sutil y tenue
    # ▁ (lower eighth block) para vacío
    bar = color + ("░" * filled) + reset + ("▁" * empty)
    return bar

def claude_usage_bar():
    """
    Función principal que Claude Code ejecuta para mostrar el status bar
    Lee JSON de stdin y muestra: [████████░░] 75% Reset: Sat 00:00
    """
    try:
        # Leer JSON de stdin (Claude Code pasa datos de la sesión)
        input_data = sys.stdin.read().strip()
        if not input_data:
            return ""

        data = json.loads(input_data)

        # DEBUG: Guardar datos recibidos para análisis
        debug_file = os.path.expanduser("~/.claude-code/statusbar-debug.json")
        try:
            with open(debug_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

        # Extraer información de la sesión
        session_id = data.get('session_id', '')
        model_info = data.get('model', {})

        # PRIORIDAD 1: Intentar obtener datos reales desde claude.ai
        web_percentage, web_reset_time = get_web_usage_data()

        if web_percentage is not None:
            # Usar datos de la web (más precisos)
            percentage = web_percentage
            reset_time = web_reset_time if web_reset_time else calculate_session_reset(session_id)
        else:
            # FALLBACK: Calcular localmente si no hay datos de la web
            context_limit = get_context_limit(model_info)

            # Leer tokens del archivo JSONL de la sesión
            input_tokens, output_tokens, cache_creation, cache_read = get_session_tokens(session_id)

            # Calcular total de tokens
            usage_tokens = input_tokens + output_tokens + cache_creation

            # Si no hay datos de tokens, mostrar mensaje básico
            if usage_tokens == 0:
                plan = get_plan_name(model_info)
                return f"Claude Code ({plan})"

            # Calcular porcentaje de uso
            percentage = min(int((usage_tokens / context_limit) * 100), 100)

        # Calcular reset time desde el primer mensaje de la sesión
        reset_time = calculate_session_reset(session_id)

        # Calcular ancho dinámico de la terminal
        terminal_width = get_terminal_width()
        if terminal_width < 50:
            terminal_width = 50

        # Preparar strings de información
        color = get_color_code(percentage)
        reset_color = "\033[0m"

        perc_str = f"{color}{percentage}%{reset_color}"
        reset_display = f"Resets: {reset_time}"

        # Calcular ancho disponible para la barra
        # Formato simplificado: "[bar] XX% Resets: HH:MM"
        # Nota: Los códigos de color no cuentan para el ancho visual
        fixed_width = 4 + len(f"{percentage}%") + 1 + len(reset_display)
        bar_width = max(terminal_width - fixed_width, 10)

        # Crear barra de progreso
        progress_bar = create_progress_bar(percentage, bar_width)

        # Retornar línea completa: [░░░░░▁▁▁] 77% Resets: 18:00
        return f"[{progress_bar}] {perc_str} {reset_display}"

    except Exception as e:
        # En caso de error, mostrar mensaje genérico
        return f"Claude Code (Error: {str(e)[:20]})"

# --- IMPORTANTE: No modificar esta línea ---
# Claude Code busca exactamente esta función para el status bar
__claude_code_status_bar__ = claude_usage_bar

# Permitir ejecución directa para pruebas
if __name__ == "__main__":
    result = claude_usage_bar()
    if result:
        print(result)
