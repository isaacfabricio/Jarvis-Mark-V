import asyncio
import websockets
import json
import speech_recognition as sr
import edge_tts
import pygame
import os
import psutil
from dotenv import load_dotenv

load_dotenv()
TOKEN_SECRETO = os.getenv("JARVIS_TOKEN", "token_padrao_seguro")
SERVIDOR_URL = os.getenv("JARVIS_SERVER_URL", "ws://127.0.0.1:8000")

async def reproduzir_audio(texto: str):
    """Sintetiza a voz com controle seguro de inicialização de áudio."""
    arquivo = "resposta_jarvis.mp3"
    try:
        comunicador = edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="-15%", pitch="-25Hz")
        await comunicador.save(arquivo)
        
        pygame.mixer.init()
        pygame.mixer.music.load(arquivo)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except Exception as e:
        print(f"[ERRO DE ÁUDIO]: {e}")
    finally:
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
            except:
                pass

def ouvir_microfone_sync():
    reconhecedor = sr.Recognizer()
    reconhecedor.dynamic_energy_threshold = True
    with sr.Microphone() as fonte:
        reconhecedor.adjust_for_ambient_noise(fonte, duration=0.5)
        try:
            audio = reconhecedor.listen(fonte, timeout=5, phrase_time_limit=10)
            return reconhecedor.recognize_google(audio, language="pt-BR")
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return None
        except Exception as e:
            print(f"[ERRO DE MICROFONE]: {e}")
            return None

async def loop_telemetria(websocket):
    while True:
        try:
            pacote = {
                "tipo": "telemetria",
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent
            }
            await websocket.send(json.dumps(pacote))
        except Exception:
            break
        await asyncio.sleep(3)

async def escutar_cerebro(websocket):
    async for mensagem in websocket:
        try:
            dados = json.loads(mensagem)
            if dados.get("acao") == "falar":
                texto = dados.get("log", "")
                print(f"[JARVIS]: {texto}")
                await reproduzir_audio(texto)
        except Exception as e:
            print(f"[ERRO AO PROCESSAR MENSAGEM DO CÉREBRO]: {e}")

async def escutar_usuario(websocket):
    while True:
        comando = await asyncio.to_thread(ouvir_microfone_sync)
        if comando and "jarvis" in comando.lower():
            print(f"[USUÁRIO]: {comando}")
            pacote = {"tipo": "comando", "comando": comando}
            try:
                await websocket.send(json.dumps(pacote))
            except Exception:
                break
        await asyncio.sleep(0.5)

async def main():
    url = f"{SERVIDOR_URL}/ws/{TOKEN_SECRETO}"
    tentativa = 0
    
    print("\n" + "="*50)
    print("🦾 AGENTE WINDOWS (MARK V PRO) // INICIALIZANDO...")
    print("="*50 + "\n")
    
    while True:
        try:
            tentativa += 1
            print(f"🔄 Conectando ao Cérebro Central (Tentativa {tentativa})... [{url}]")
            async with websockets.connect(url) as websocket:
                print("✅ Conectado ao Cérebro Central com Sucesso!")
                tentativa = 0 # Reseta contador ao conectar
                await asyncio.gather(
                    escutar_cerebro(websocket),
                    escutar_usuario(websocket),
                    loop_telemetria(websocket)
                )
        except websockets.exceptions.ConnectionClosed as e:
            print(f"⚠️ Conexão perdida com o Cérebro (Código: {e.code}). Tentando reconectar...")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
        
        # Backoff exponencial limitado a 30 segundos
        tempo_espera = min(30, 2 ** min(tentativa, 5))
        print(f"⏳ Aguardando {tempo_espera} segundos para nova tentativa...")
        await asyncio.sleep(tempo_espera)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Agente Windows encerrado pelo usuário.")
