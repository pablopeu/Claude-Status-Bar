#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timedelta
import os

def read_first_message_time(transcript_path):
    """Lee el transcript y obtiene el timestamp del primer mensaje"""
    if not transcript_path or not os.path.exists(transcript_path):
        return None

    try:
        with open(transcript_path, 'r') as f:
            # El transcript es JSONL (una línea JSON por registro)
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # Buscar el primer mensaje con timestamp
                    if 'timestamp' in entry:
                        ts = entry['timestamp']
                        # El timestamp puede estar en milisegundos (Unix epoch)
                        if isinstance(ts, (int, float)):
                            return datetime.fromtimestamp(ts / 1000)
                        # O en formato ISO
                        else:
                            return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception as e:
        pass

    return None

def format_time_remaining(hours, minutes):
    """Formatea el tiempo restante"""
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def create_progress_bar(percentage, width=20):
    """Crea una barra de progreso visual"""
    filled = int(width * percentage / 100)
    empty = width - filled

    # Caracteres de la barra
    bar = '█' * filled + '░' * empty

    # Colores según porcentaje
    if percentage < 50:
        color = '\033[32m'  # Verde
    elif percentage < 80:
        color = '\033[33m'  # Amarillo
    else:
        color = '\033[31m'  # Rojo

    reset_color = '\033[0m'

    return f"{color}[{bar}] {percentage}%{reset_color}"

def main():
    # Leer JSON de entrada
    try:
        data = json.load(sys.stdin)
    except Exception:
        print("Error reading input")
        return

    # Extraer información del context window
    context_window = data.get('context_window', {})
    total_input = context_window.get('total_input_tokens', 0)
    total_output = context_window.get('total_output_tokens', 0)
    context_size = context_window.get('context_window_size', 200000)

    # Calcular porcentaje de contexto usado
    total_tokens = total_input + total_output
    if context_size > 0:
        context_percent = min(int((total_tokens / context_size) * 100), 100)
    else:
        context_percent = 0

    # Obtener timestamp del primer mensaje para calcular reset time
    transcript_path = data.get('transcript_path')
    first_message_time = read_first_message_time(transcript_path)

    reset_info = ""
    if first_message_time:
        # Hora actual
        now = datetime.now()

        # La sesión resetea 5 horas después del primer mensaje
        reset_time = first_message_time + timedelta(hours=5)

        if reset_time > now:
            time_remaining = reset_time - now
            hours = int(time_remaining.total_seconds() // 3600)
            minutes = int((time_remaining.total_seconds() % 3600) // 60)
            reset_info = f" Resets: {format_time_remaining(hours, minutes)}"
        else:
            reset_info = " Resets: Now"

    # Crear barra de progreso
    progress_bar = create_progress_bar(context_percent)

    # Output final
    print(f"{progress_bar}{reset_info}")

if __name__ == '__main__':
    main()
