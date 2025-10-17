"""
Script de teste para verificar a instalação do SimPy
"""
import simpy

def test_installation():
    """Teste simples para verificar se o SimPy está funcionando"""
    env = simpy.Environment()
    
    def process(env):
        print(f'Iniciando processo no tempo {env.now}')
        yield env.timeout(5)
        print(f'Processo finalizado no tempo {env.now}')
    
    env.process(process(env))
    env.run()
    
    print("\n✓ SimPy está instalado e funcionando corretamente!")
    print(f"✓ Versão do SimPy: {simpy.__version__}")

if __name__ == '__main__':
    test_installation()

