
#Fica aqui guardado just in case................obsoleto neste momento

import sys
import importlib
import pkgutil

print("🔍 Verificação de módulos 'player' carregados:\n")

# mostra módulos no sys.modules que contenham "player"
for name, mod in sys.modules.items():
    if "player" in name.lower():
        try:
            print(f"{name:<40} -> {getattr(mod, '__file__', 'built-in')}")
        except Exception:
            pass

# tenta encontrar módulos 'player' no diretório atual
print("\n🔍 Pesquisa no diretório atual:")
for finder, name, ispkg in pkgutil.iter_modules():
    if "player" in name.lower():
        print(f"Encontrado módulo '{name}' (pkg={ispkg}) em {finder.path}")
