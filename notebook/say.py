#!/usr/bin/env python3
"""
say.py — Gera áudio WAV a partir de texto usando o Piper TTS (PT-BR).

Uso:
    python say.py "Velocidade máxima excedida" --play
    python say.py "Ignição ligada" --output ignição.wav
    python say.py --list-frases --play
    python say.py --demo          (modo interativo: digita e ouve na hora)

O modelo de voz é baixado automaticamente na primeira execução (precisa de internet).
Depois disso, funciona 100% offline.
"""

import argparse
import sys
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

MODELS_DIR = Path(__file__).parent / "models"

# Modelo padrão: faber (masculino, boa qualidade, tamanho médio)
# Alternativas PT-BR disponíveis no Hugging Face rhasspy/piper-voices:
#   pt_BR-faber-medium   (~63 MB) — masculino, qualidade boa
#   pt_BR-cadu-medium    (~63 MB) — masculino
#   pt_BR-edresson-low   (~29 MB) — masculino, qualidade menor, arquivo menor
DEFAULT_MODEL = "pt_BR-faber-medium"

MODEL_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR"

MODEL_FILES = {
    "pt_BR-faber-medium": [
        "faber/medium/pt_BR-faber-medium.onnx",
        "faber/medium/pt_BR-faber-medium.onnx.json",
    ],
    "pt_BR-cadu-medium": [
        "cadu/medium/pt_BR-cadu-medium.onnx",
        "cadu/medium/pt_BR-cadu-medium.onnx.json",
    ],
    "pt_BR-edresson-low": [
        "edresson/low/pt_BR-edresson-low.onnx",
        "edresson/low/pt_BR-edresson-low.onnx.json",
    ],
}

FRASES_TESTE = [
    # Alertas de velocidade
    "Atenção! Velocidade máxima excedida.",
    "Velocidade normalizada.",
    # Estado operacional da máquina
    "Máquina em operação produtiva.",
    "Máquina em estado alternativo.",
    "Máquina parada.",
    "Máquina em trânsito.",
    # Ignição
    "Ignição ligada.",
    "Ignição desligada.",
    # Erros de sistema
    "Sinal de GPS perdido.",
    "Erro no cartão de memória.",
    "Comunicação CAN inativa.",
    "Comunicação CAN ativa.",
    # Leitor de cartão (track v2)
    "Acesso liberado.",
    "Cartão não reconhecido.",
    "Acesso negado.",
]

# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def check_piper():
    try:
        import piper
        return True
    except ImportError:
        return False


def install_piper():
    print("piper-tts não encontrado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "piper-tts"])
    print("piper-tts instalado.\n")


def download_model(model_name: str) -> tuple[Path, Path]:
    """Baixa o modelo se não existir localmente. Retorna (onnx_path, config_path)."""
    if model_name not in MODEL_FILES:
        print(f"Modelo '{model_name}' desconhecido.")
        print(f"Modelos disponíveis: {', '.join(MODEL_FILES)}")
        sys.exit(1)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    onnx_path = None
    config_path = None

    for remote_path in MODEL_FILES[model_name]:
        filename = remote_path.split("/")[-1]
        local_path = MODELS_DIR / filename
        url = f"{MODEL_BASE_URL}/{remote_path}"

        if local_path.exists():
            print(f"  [ok] {filename} já existe localmente.")
        else:
            print(f"  Baixando {filename}...")
            try:
                urllib.request.urlretrieve(url, local_path, _progress_hook)
                print()
            except Exception as e:
                print(f"\nErro ao baixar {url}: {e}")
                print("Verifique sua conexão com a internet e tente novamente.")
                sys.exit(1)

        if filename.endswith(".onnx.json"):
            config_path = local_path
        elif filename.endswith(".onnx"):
            onnx_path = local_path

    return onnx_path, config_path


def _progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(downloaded / total_size * 100, 100)
        bar = "#" * int(pct / 2)
        print(f"\r  [{bar:<50}] {pct:5.1f}%", end="", flush=True)


def play_wav(path: Path):
    """Toca um arquivo WAV pelo alto-falante do sistema."""
    if sys.platform == "win32":
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME)
    elif sys.platform == "darwin":
        subprocess.run(["afplay", str(path)], check=True)
    else:
        # Linux: tenta aplay (ALSA), depois paplay (PulseAudio)
        for player in ("aplay", "paplay"):
            if subprocess.run(["which", player], capture_output=True).returncode == 0:
                subprocess.run([player, str(path)], check=True)
                return
        print("  (nenhum player de áudio encontrado — instale 'aplay' ou 'paplay')")


def synthesize(text: str, onnx_path: Path, config_path: Path, output_path: Path):
    """Sintetiza o texto e salva como WAV."""
    from piper import PiperVoice
    import wave

    voice = PiperVoice.load(str(onnx_path), config_path=str(config_path))

    with wave.open(str(output_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)


def synthesize_and_play(text: str, onnx_path: Path, config_path: Path, output_path: Path | None = None):
    """Sintetiza e toca o áudio. Se output_path for None, usa arquivo temporário."""
    use_temp = output_path is None
    if use_temp:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = Path(tmp.name)
        tmp.close()

    try:
        synthesize(text, onnx_path, config_path, output_path)
        play_wav(output_path)
    finally:
        if use_temp:
            output_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Modos de operação
# ---------------------------------------------------------------------------

def _load(model_name: str):
    """Garante dependências e retorna (onnx_path, config_path)."""
    if not check_piper():
        install_piper()
    print(f"Modelo: {model_name}")
    return download_model(model_name)


def mode_demo(onnx_path: Path, config_path: Path):
    """Modo interativo: digita uma frase, ouve na hora."""
    print("\n--- Modo demo Simova Track ---")
    print("Digite uma frase e pressione Enter para ouvir.")
    print("Deixe em branco e pressione Enter para sair.\n")
    while True:
        try:
            text = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        print(f"  Sintetizando...", end=" ", flush=True)
        synthesize_and_play(text, onnx_path, config_path)
        print("ok")
    print("\nEncerrando.")


def mode_list(onnx_path: Path, config_path: Path, play: bool):
    """Gera (e opcionalmente toca) todas as frases de teste."""
    out_dir = Path("frases")
    out_dir.mkdir(exist_ok=True)
    print(f"\nGerando {len(FRASES_TESTE)} frases em ./{out_dir}/\n")
    for frase in FRASES_TESTE:
        slug = (frase.lower()
                .replace(" ", "_").replace(",", "")
                .replace(".", "").replace("!", ""))
        out_file = out_dir / f"{slug}.wav"
        print(f"  {frase}")
        synthesize(frase, onnx_path, config_path, out_file)
        if play:
            play_wav(out_file)
    print("\nPronto.")


def mode_single(text: str, output_path: Path, onnx_path: Path, config_path: Path, play: bool):
    """Sintetiza uma frase e salva."""
    print(f'\nSintetizando: "{text}"')
    synthesize(text, onnx_path, config_path, output_path)
    size_kb = output_path.stat().st_size / 1024
    print(f"Salvo em: {output_path}  ({size_kb:.1f} KB)")
    if play:
        play_wav(output_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Gera áudio WAV a partir de texto usando Piper TTS (PT-BR)."
    )
    parser.add_argument("texto", nargs="?", help="Texto a sintetizar.")
    parser.add_argument("--output", "-o", default="output.wav",
                        help="Arquivo WAV de saída (padrão: output.wav).")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        choices=list(MODEL_FILES.keys()),
                        help=f"Modelo de voz (padrão: {DEFAULT_MODEL}).")
    parser.add_argument("--list-frases", action="store_true",
                        help="Gera todas as frases de teste do produto.")
    parser.add_argument("--play", "-p", action="store_true",
                        help="Toca o áudio pelo alto-falante após gerar.")
    parser.add_argument("--demo", action="store_true",
                        help="Modo interativo: digita qualquer frase e ouve na hora.")
    args = parser.parse_args()

    if not args.texto and not args.list_frases and not args.demo:
        parser.print_help()
        sys.exit(1)

    onnx_path, config_path = _load(args.model)

    if args.demo:
        mode_demo(onnx_path, config_path)
    elif args.list_frases:
        mode_list(onnx_path, config_path, play=args.play)
    else:
        mode_single(args.texto, Path(args.output), onnx_path, config_path, play=args.play)


if __name__ == "__main__":
    main()
