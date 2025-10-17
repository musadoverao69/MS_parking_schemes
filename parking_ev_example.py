"""
Exemplo inicial de simulação: Estacionamento com vagas para veículos elétricos
Cenário 4.1: Esquemas de estacionamento em shopping

Este exemplo demonstra um sistema básico de estacionamento onde:
- Há vagas regulares e vagas com estações de recarga para veículos elétricos
- Veículos chegam em intervalos aleatórios
- Alguns veículos são elétricos e precisam de recarga
"""
import simpy
import random

# Configurações da simulação
RANDOM_SEED = 42
NUM_VAGAS_REGULARES = 50
NUM_VAGAS_EV = 10  # Vagas com estação de recarga
TEMPO_SIMULACAO = 480  # 8 horas em minutos
INTERVALO_CHEGADA = 5  # Minutos entre chegadas (média)
PROB_VEICULO_EV = 0.3  # 30% dos veículos são elétricos
TEMPO_ESTACIONAMENTO = (30, 120)  # Min e max em minutos


class EstacionamentoShopping:
    """Representa um estacionamento de shopping com vagas para veículos elétricos"""
    
    def __init__(self, env, num_vagas_regulares, num_vagas_ev):
        self.env = env
        self.vagas_regulares = simpy.Resource(env, capacity=num_vagas_regulares)
        self.vagas_ev = simpy.Resource(env, capacity=num_vagas_ev)
        
        # Estatísticas
        self.total_veiculos = 0
        self.total_veiculos_ev = 0
        self.veiculos_atendidos = 0
        self.veiculos_ev_atendidos = 0
        self.veiculos_rejeitados = 0
        self.tempo_espera_total = 0
        
    def imprimir_status(self):
        """Imprime o status atual do estacionamento"""
        print(f"\n[Tempo {self.env.now:.0f}min] Status do Estacionamento:")
        print(f"  Vagas regulares ocupadas: {self.vagas_regulares.count}/{self.vagas_regulares.capacity}")
        print(f"  Vagas EV ocupadas: {self.vagas_ev.count}/{self.vagas_ev.capacity}")
        print(f"  Fila vagas regulares: {len(self.vagas_regulares.queue)}")
        print(f"  Fila vagas EV: {len(self.vagas_ev.queue)}")


def veiculo(env, nome, estacionamento, is_ev):
    """Processo de um veículo chegando ao estacionamento"""
    tipo = "EV" if is_ev else "Regular"
    chegada = env.now
    
    print(f'[{env.now:.0f}min] {nome} ({tipo}) chegou ao estacionamento')
    
    # Veículos elétricos tentam usar vagas EV primeiro
    if is_ev:
        # Verificar se há vagas EV disponíveis
        if estacionamento.vagas_ev.count < estacionamento.vagas_ev.capacity or len(estacionamento.vagas_ev.queue) < 2:
            vaga = estacionamento.vagas_ev
            tipo_vaga = "EV"
        else:
            # Se não houver vagas EV, usar vaga regular
            vaga = estacionamento.vagas_regulares
            tipo_vaga = "Regular (fallback)"
    else:
        vaga = estacionamento.vagas_regulares
        tipo_vaga = "Regular"
    
    # Tentar obter uma vaga
    with vaga.request() as pedido:
        yield pedido
        
        tempo_espera = env.now - chegada
        estacionamento.tempo_espera_total += tempo_espera
        
        print(f'[{env.now:.0f}min] {nome} estacionou em vaga {tipo_vaga} (esperou {tempo_espera:.0f}min)')
        
        # Tempo de permanência no estacionamento
        tempo_permanencia = random.randint(*TEMPO_ESTACIONAMENTO)
        yield env.timeout(tempo_permanencia)
        
        print(f'[{env.now:.0f}min] {nome} saiu do estacionamento (permaneceu {tempo_permanencia:.0f}min)')
        
        estacionamento.veiculos_atendidos += 1
        if is_ev:
            estacionamento.veiculos_ev_atendidos += 1


def gerador_veiculos(env, estacionamento):
    """Gera veículos chegando ao estacionamento"""
    contador = 0
    
    while True:
        # Intervalo entre chegadas (distribuição exponencial)
        yield env.timeout(random.expovariate(1.0 / INTERVALO_CHEGADA))
        
        contador += 1
        is_ev = random.random() < PROB_VEICULO_EV
        
        estacionamento.total_veiculos += 1
        if is_ev:
            estacionamento.total_veiculos_ev += 1
        
        # Criar processo do veículo
        env.process(veiculo(env, f'Veículo-{contador}', estacionamento, is_ev))


def monitor_status(env, estacionamento, intervalo=60):
    """Monitora e imprime o status do estacionamento periodicamente"""
    while True:
        yield env.timeout(intervalo)
        estacionamento.imprimir_status()


def main():
    """Função principal da simulação"""
    print("=" * 70)
    print("SIMULAÇÃO: Estacionamento de Shopping com Vagas para Veículos Elétricos")
    print("=" * 70)
    print(f"\nConfiguração:")
    print(f"  - Vagas regulares: {NUM_VAGAS_REGULARES}")
    print(f"  - Vagas com recarga EV: {NUM_VAGAS_EV}")
    print(f"  - Tempo de simulação: {TEMPO_SIMULACAO} minutos ({TEMPO_SIMULACAO/60:.1f} horas)")
    print(f"  - Probabilidade de veículo EV: {PROB_VEICULO_EV*100:.0f}%")
    print(f"  - Intervalo médio entre chegadas: {INTERVALO_CHEGADA} minutos")
    print("\n" + "=" * 70)
    
    # Configurar seed para reprodutibilidade
    random.seed(RANDOM_SEED)
    
    # Criar ambiente de simulação
    env = simpy.Environment()
    
    # Criar estacionamento
    estacionamento = EstacionamentoShopping(env, NUM_VAGAS_REGULARES, NUM_VAGAS_EV)
    
    # Iniciar processos
    env.process(gerador_veiculos(env, estacionamento))
    env.process(monitor_status(env, estacionamento, intervalo=120))
    
    # Executar simulação
    env.run(until=TEMPO_SIMULACAO)
    
    # Estatísticas finais
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS FINAIS")
    print("=" * 70)
    print(f"Total de veículos que chegaram: {estacionamento.total_veiculos}")
    print(f"  - Veículos regulares: {estacionamento.total_veiculos - estacionamento.total_veiculos_ev}")
    print(f"  - Veículos elétricos: {estacionamento.total_veiculos_ev}")
    print(f"\nVeículos atendidos: {estacionamento.veiculos_atendidos}")
    print(f"  - Veículos EV atendidos: {estacionamento.veiculos_ev_atendidos}")
    
    if estacionamento.veiculos_atendidos > 0:
        tempo_medio_espera = estacionamento.tempo_espera_total / estacionamento.veiculos_atendidos
        print(f"\nTempo médio de espera: {tempo_medio_espera:.2f} minutos")
    
    taxa_utilizacao_regular = (estacionamento.vagas_regulares.count / estacionamento.vagas_regulares.capacity) * 100
    taxa_utilizacao_ev = (estacionamento.vagas_ev.count / estacionamento.vagas_ev.capacity) * 100
    
    print(f"\nTaxa de utilização final:")
    print(f"  - Vagas regulares: {taxa_utilizacao_regular:.1f}%")
    print(f"  - Vagas EV: {taxa_utilizacao_ev:.1f}%")
    print("=" * 70)


if __name__ == '__main__':
    main()

