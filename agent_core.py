# agent_core.py
from anthropic import Anthropic
client = Anthropic()

def crear_agente(context_module):
    historial = []

    class Agente:
        nombre = getattr(context_module, 'NOMBRE', 'Agente')
        
        def preguntar(self, mensaje):
            datos = context_module.get_data_context()
            system = context_module.SYSTEM_PROMPT + "\n\n" + datos
            historial.append({"role": "user", "content": mensaje})
            r = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                system=system,
                messages=historial
            )
            resp = r.content[0].text
            historial.append({"role": "assistant", "content": resp})
            return resp
        
        def limpiar(self):
            historial.clear()

    return Agente()

def chat_interactivo(context_module):
    agente = crear_agente(context_module)
    nombre = agente.nombre
    print(f"\n{'='*50}\n  {nombre}  escribi salir para terminar\n{'='*50}\n")
    while True:
        try: entrada = input("Vos: ").strip()
        except: break
        if not entrada: continue
        if entrada.lower() == 'salir': break
        if entrada.lower() == 'limpiar':
            agente.limpiar()
            print("[Conversacion reiniciada]\n")
            continue
        print(f"\n{nombre}: {agente.preguntar(entrada)}\n")

if __name__ == "__main__":
    print("1. El Pasaje\n2. SIA")
    op = input("Opcion: ").strip()
    if op == "1": import context_elpasaje as ctx
    elif op == "2": import context_sia as ctx
    else: exit()
    chat_interactivo(ctx)
