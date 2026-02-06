# Layer 7 Offensive Suite (Simuladores de Ataque)

Esta suite contém ferramentas desenvolvidas para simular ataques de Camada 7 (Aplicação) com o objetivo de testar a resiliência de servidores web, APIs e firewalls (WAF).

## ⚠️ AVISO LEGAL (DISCLAIMER)

**ESTAS FERRAMENTAS SÃO DESTINADAS ESTRITAMENTE PARA FINS EDUCACIONAIS E DE TESTE EM AMBIENTES AUTORIZADOS.**

O uso destes scripts contra alvos sem permissão explícita é ILEGAL e antiético. O autor e o projeto não se responsabilizam pelo mau uso destas ferramentas.

## Ferramentas Incluídas

1.  **http_flood_simulator.py**: Simula inundações de requisições HTTP (GET/POST) para testar a capacidade de processamento do servidor.
2.  **slowloris_simulator.py**: Simula ataques de negação de serviço "lentos", mantendo conexões abertas o máximo possível para exaurir a pool de threads do servidor.
3.  **api_abuse_simulator.py**: Simula uso abusivo de endpoints de API, incluindo rotação de tokens simulada.
4.  **session_exhaustion_simulator.py**: Gera um grande número de novas sessões/cookies para testar o gerenciamento de estado do servidor.
5.  **websocket_flood_simulator.py**: Simula conexões massivas e envio de mensagens via WebSocket.

## Requisitos

*   Python 3.x
*   Nenhuma biblioteca externa obrigatória (apenas bibliotecas padrão do Python).

## Uso

Cada script possui um menu de ajuda (`-h` ou `--help`).

Exemplo:
```bash
python3 http_flood_simulator.py --help
```


## Ferramentas Adicionais (Avançadas)

6.  **bot_behavior_emulator.py**: Emula assinaturas de bots conhecidos (Googlebot, Bingbot) e padrões de timing humanos/robóticos.
7.  **distributed_pattern_simulator.py**: Simula ataques distribuídos usando listas de proxies (se fornecidas) ou spoofing de headers (Client-IP, X-Forwarded-For).
8.  **request_entropy_attack_simulator.py**: Gera requisições com alta entropia (URLs e Headers aleatórios) para tentar evadir regras de WAF baseadas em assinaturas estáticas.
9.  **cache_bypass_simulator.py**: Utiliza técnicas de "Cache Busting" (parâmetros únicos, headers no-cache) para forçar o processamento no backend, ignorando caches intermediários (CDNs).
10. **layer7_attack_orchestrator.py**: Script mestre para orquestrar múltiplos simuladores simultaneamente, criando cenários complexos (Ex: Stress, Evasion, Stealth).

## Exemplo de Orquestração

Para rodar um cenário de evasão combinado:
```bash
python3 layer7_attack_orchestrator.py http://alvo.com --scenario evasion --duration 120
```
