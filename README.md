# Projeto de Simulação e Modelagem - E-Mobility

## Descrição do Projeto

**Tópico 4:** Distribuição e esquemas de uso de estações de recarga para e-mobilidade

Com o advento da mobilidade elétrica (carros, scooters, bicicletas, etc), a demanda por estações de recarga está aumentando consideravelmente. Este projeto visa analisar esquemas de distribuição e uso para e-mobilidade.

### Cenário 4.1: Esquemas de Estacionamento

Estacionamentos podem implementar diferentes esquemas para acomodar usuários de veículos elétricos. Considere, por exemplo, um shopping que pode reservar um certo número de vagas para veículos elétricos. Como essas vagas são alocadas aos clientes? Esquemas sob demanda, exclusividade e prioridade podem ser considerados.

---

## Instalação

### Requisitos

- Python 3.8 ou superior
- SimPy 4.1.1

### Instalando o SimPy

```bash
pip3 install simpy
```

### Verificando a Instalação

Execute o script de teste:

```bash
python3 test_simpy.py
```

---

## Estrutura do Projeto

```
Simulation/
├── README.md                 # Este arquivo
├── test_simpy.py            # Script de teste da instalação do SimPy
├── parking_ev_example.py    # Exemplo inicial de simulação de estacionamento
└── (arquivos futuros)
```

---

## Exemplos

### Exemplo 1: Estacionamento Básico com Vagas EV

O arquivo `parking_ev_example.py` demonstra uma simulação básica de um estacionamento de shopping com:

- Vagas regulares
- Vagas dedicadas para veículos elétricos (com estações de recarga)
- Chegada aleatória de veículos (regulares e elétricos)
- Estatísticas de uso e tempo de espera

**Executar:**

```bash
python3 parking_ev_example.py
```

**Parâmetros configuráveis:**
- `NUM_VAGAS_REGULARES`: Número de vagas regulares
- `NUM_VAGAS_EV`: Número de vagas com estação de recarga
- `TEMPO_SIMULACAO`: Duração da simulação em minutos
- `INTERVALO_CHEGADA`: Intervalo médio entre chegadas de veículos
- `PROB_VEICULO_EV`: Probabilidade de um veículo ser elétrico
- `TEMPO_ESTACIONAMENTO`: Tempo mínimo e máximo de permanência

---

## Próximos Passos

### Esquemas de Alocação a Implementar:

1. **Esquema Sob Demanda (On-Demand)**
   - Vagas EV são alocadas conforme necessário
   - Sem reservas antecipadas

2. **Esquema de Exclusividade**
   - Vagas EV são exclusivas para veículos elétricos
   - Veículos regulares não podem usar vagas EV mesmo se estiverem vazias

3. **Esquema de Prioridade**
   - Veículos elétricos têm prioridade para vagas EV
   - Se não houver vagas EV disponíveis, podem usar vagas regulares
   - Vagas EV vazias podem ser usadas por veículos regulares temporariamente

4. **Esquema Híbrido**
   - Combinação dos esquemas acima com regras específicas

---

## Métricas de Análise

Para cada esquema, analisaremos:

- Taxa de utilização das vagas (regulares vs EV)
- Tempo médio de espera por tipo de veículo
- Taxa de rejeição/desistência
- Satisfação dos usuários
- Eficiência energética
- Receita potencial

---

## Referências

- [SimPy Documentation](https://simpy.readthedocs.io/)
- [SimPy Examples](https://simpy.readthedocs.io/en/latest/examples/index.html)

---

## Autor

Projeto desenvolvido para a disciplina de Simulação e Modelagem - 2025

