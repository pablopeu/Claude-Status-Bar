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
from datetime import datetime, timedelta

def get_terminal_width():
    """Obtiene el ancho actual de la terminal"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def get_context_limit(model_info):
    """
    Determina el límite de contexto según el modelo
    - Sonnet 4.5: 1M tokens
    - Otros modelos: 200K tokens
    """
    if not model_info:
        return 200_000

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    # Detectar Sonnet 4.5 (1M context)
    if 'sonnet-4-5' in model_id or 'sonnet 4.5' in model_name or 'claude-sonnet-4-5' in model_id:
        return 1_000_000

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

def calculate_next_reset():
    """
    Calcula el próximo reset de Claude Code
    Los límites se resetean cada 5 horas en bloques:
    00:00-05:00, 05:00-10:00, 10:00-15:00, 15:00-20:00, 20:00-01:00 (siguiente día)
    """
    now = datetime.now()
    current_hour = now.hour

    # Determinar el próximo bloque de 5 horas
    if current_hour < 5:
        reset_hour = 5
        reset_day = now
    elif current_hour < 10:
        reset_hour = 10
        reset_day = now
    elif current_hour < 15:
        reset_hour = 15
        reset_day = now
    elif current_hour < 20:
        reset_hour = 20
        reset_day = now
    else:  # >= 20
        reset_hour = 0
        reset_day = now + timedelta(days=1)

    next_reset = reset_day.replace(hour=reset_hour, minute=0, second=0, microsecond=0)

    # Formato: "Sat 15:00" o "Today 15:00"
    if next_reset.date() == now.date():
        return f"Today {next_reset.strftime('%H:%M')}"
    elif next_reset.date() == (now + timedelta(days=1)).date():
        return f"Tmrw {next_reset.strftime('%H:%M')}"
    else:
        return next_reset.strftime("%a %H:%M")

def create_progress_bar(percentage, width):
    """Crea la barra de progreso con caracteres Unicode"""
    filled = int(percentage * width / 100)
    empty = width - filled
    return "█" * filled + "░" * empty

def get_token_usage_from_transcript(transcript_path):
    """
    Lee el transcript de la sesión actual y calcula el uso de tokens
    """
    try:
        if not os.path.exists(transcript_path):
            return None, None

        with open(transcript_path, 'r') as f:
            transcript = json.load(f)

        # Contar tokens de todos los mensajes
        total_input_tokens = 0
        total_output_tokens = 0

        for message in transcript.get('messages', []):
            # Sumar tokens de input (user + context)
            if 'inputTokens' in message:
                total_input_tokens += message['inputTokens']

            # Sumar tokens de output (assistant)
            if 'outputTokens' in message:
                total_output_tokens += message['outputTokens']

        # El total usado es principalmente los input tokens (que incluyen el contexto)
        return total_input_tokens, total_output_tokens
    except:
        return None, None

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

        # Extraer información del modelo
        model_info = data.get('model', {})

        # Determinar límite de contexto según el modelo
        context_limit = get_context_limit(model_info)

        # Intentar obtener tokens de varias fuentes
        usage_tokens = 0

        # Método 1: Campos directos en data
        current_tokens = data.get('current_tokens', 0)
        expected_total_tokens = data.get('expected_total_tokens', 0)
        input_tokens = data.get('inputTokens', 0)

        # Método 2: Leer desde el transcript
        transcript_path = data.get('transcript_path', '')
        if transcript_path:
            input_tok, output_tok = get_token_usage_from_transcript(transcript_path)
            if input_tok:
                usage_tokens = input_tok

        # Método 3: Usar campos directos si están disponibles
        if not usage_tokens:
            if current_tokens > 0:
                usage_tokens = current_tokens
            elif expected_total_tokens > 0:
                usage_tokens = expected_total_tokens
            elif input_tokens > 0:
                usage_tokens = input_tokens

        # Si no hay datos de tokens, mostrar plan por defecto
        if usage_tokens == 0:
            plan = get_plan_name(model_info)
            return f"Claude Code ({plan})"

        # Calcular porcentaje de uso
        percentage = min(int((usage_tokens / context_limit) * 100), 100)

        # Calcular ancho dinámico de la terminal
        terminal_width = get_terminal_width()
        if terminal_width < 50:
            terminal_width = 50

        # Preparar strings de información
        perc_str = f"{percentage}%"
        reset_str = f"Reset: {calculate_next_reset()}"

        # Calcular ancho disponible para la barra
        # Formato: "[bar] XX% Reset: Xxx XX:XX"
        # Espacios: "[" + "]" + " " + perc_str + " " + reset_str = 4 + len(perc_str) + len(reset_str)
        fixed_width = 4 + len(perc_str) + len(reset_str)
        bar_width = max(terminal_width - fixed_width, 10)

        # Crear barra de progreso
        progress_bar = create_progress_bar(percentage, bar_width)

        # Retornar línea completa: [████░░] 75% Reset: Today 15:00
        return f"[{progress_bar}] {perc_str} {reset_str}"

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
