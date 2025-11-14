# 🎨 Visualização do Parking Lot

Documentação sobre opções de visualização para o simulador de parking lot.

---

## 📊 Visualização Implementada

### **Pygame** 🎮 Estilo Highway-Env
**Vantagens:**
- ✅ Muito interativo
- ✅ Controle total sobre gráficos
- ✅ Estilo similar a highway-env
- ✅ Boa performance

**Desvantagens:**
- ⚠️ Requer mais código
- ⚠️ Dependência adicional (pygame)

**Uso:** Implementado e ativo no projeto

---

## 🚀 Implementação Atual

### Pygame (Estilo Highway-Env)

**Arquivo:** `visualizer_pygame.py`

**Características:**
- Visualização mais elaborada
- Carros se movem pela tela
- Animações de chegada/partida
- Controles interativos (pause, speed)
- Estilo similar a highway-env

**Integração:** Thread separada sincronizada com SimPy

---

## 📝 Como Usar

```bash
python3 simulator.py --visualize
# ou
python3 simulator.py -v
```

---

## 🔧 Arquitetura de Integração

### Método: Thread Separada (Pygame)
```python
# Thread de visualização roda paralelamente
# Sincroniza com SimPy através de queue
visualizer_queue.put(("arrive", vehicle_data))
```

---

## 🎯 O que Visualizar?

1. **Layout do Parking Lot**
   - Entrada do shopping
   - Estações de carregamento (posições)
   - Vagas regulares (área)

2. **Veículos**
   - Chegada (entrando)
   - Estacionado (cor por tipo: EV/Regular)
   - Fila de espera
   - Partida (saindo)

3. **Estatísticas em Tempo Real**
   - Tempo de simulação
   - Veículos servidos
   - Utilização das estações
   - Receita acumulada

4. **Legenda**
   - Cores: EV (verde), Regular (azul)
   - Estados: Esperando, Estacionado
   - Estações: Nome, preço, distância

---

## 📦 Dependências

### Pygame:
```bash
pip install pygame
```

Já incluído no `requirements.txt`.

---

## 🔄 Status

✅ Visualizador Pygame implementado e funcional
✅ Integração completa com SimPy
✅ Controles interativos (pausar, velocidade)
✅ Layout realista de estacionamento
✅ Animação de entrada/saída de veículos

