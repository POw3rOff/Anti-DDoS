# Scripts de Firewall para pfSense

Este diretório contém o script `pfsense_setup_rules.php` projetado para automatizar a criação de regras de firewall e hardening no pfSense.

## O que o script faz?

1.  **Cria Aliases (Listas)**:
    *   Cria um alias do tipo URL Table para blocklists (ex: Spamhaus DROP). Isso permite que o pfSense baixe e atualize automaticamente a lista de IPs maliciosos a cada 24h.
2.  **Cria Regras de Firewall**:
    *   Adiciona uma regra de **BLOQUEIO** no topo da interface WAN para todo o tráfego originado dos IPs listados nos Aliases criados.
    *   Habilita logs para esses bloqueios.
3.  **System Tunables (Hardening)**:
    *   Ajusta parâmetros do kernel (`sysctl`) como `net.pf.states_hashsize` para aumentar a resistência contra ataques de exaustão de estados (DDoS).

## Como Usar

### Aviso Importante
**Sempre faça um BACKUP da configuração do seu pfSense antes de rodar scripts automatizados.**

### Método 1: PHP Execute (Interface Web)
1.  Acesse o pfSense.
2.  Vá em **Diagnostics** > **Command Prompt**.
3.  Copie todo o conteúdo do arquivo `pfsense_setup_rules.php`.
4.  Cole na caixa de texto **PHP Execute**.
5.  Clique em **Execute**.

### Método 2: Upload e Shell (SSH)
1.  Habilite o SSH no pfSense (System > Advanced > Admin Access).
2.  Envie o arquivo para o servidor (ex: via SCP):
    ```bash
    scp pfsense_setup_rules.php root@seu-pfsense-ip:/root/
    ```
3.  Acesse via SSH e execute:
    ```bash
    pfSsh.php playback /root/pfsense_setup_rules.php
    ```

## Verificação
Após a execução, vá em **Firewall** > **Rules** > **WAN** e verifique se a regra de bloqueio foi criada no topo da lista. Verifique também em **Firewall** > **Aliases** se as listas foram criadas.

---
*Gerado por AI Assistant.*
