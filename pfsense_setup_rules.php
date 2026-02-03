<?php
/*
 * Script de Configuração de Regras de Firewall para pfSense
 * @versão 1.0.0
 * @autor AI Assistant
 *
 * INSTRUÇÕES:
 * 1. Faça backup da sua configuração atual do pfSense!
 * 2. Carregue este script para o seu pfSense (ex: /root/pfsense_setup_rules.php)
 * 3. Execute via shell SSH: pfSsh.php playback /root/pfsense_setup_rules.php
 *    OU execute no "Diagnostics > Command Prompt" > "PHP Execute".
 */

require_once("config.inc");
require_once("functions.inc");
require_once("filter.inc");
require_once("shaper.inc");
require_once("util.inc");

echo "Iniciando configuração de regras de firewall...\n";

// ----------------------------------------------------------------------
// 1. Criar Alias para Blocklists
// ----------------------------------------------------------------------
function create_alias($name, $type, $url, $descr) {
    global $config;

    // Verifica se já existe
    if (is_array($config["aliases"]["alias"])) {
        foreach ($config["aliases"]["alias"] as $alias) {
            if ($alias["name"] == $name) {
                echo "Alias $name já existe. Pulando.\n";
                return;
            }
        }
    } else {
        $config["aliases"]["alias"] = array();
    }

    $new_alias = array();
    $new_alias["name"] = $name;
    $new_alias["type"] = $type; // urltable, host, network, etc.
    $new_alias["url"] = $url;
    $new_alias["freq"] = "24"; // Atualizar a cada 24h (para urltable)
    $new_alias["descr"] = $descr;
    $new_alias["address"] = ""; // Usado para listas estáticas
    $new_alias["detail"] = "";

    $config["aliases"]["alias"][] = $new_alias;
    echo "Alias $name criado.\n";
}

// Criar Alias de Blocklist (Exemplo usando URL Table do Spamhaus)
// Nota: URL Table é a forma mais eficiente para grandes listas no pfSense
create_alias("BadIPs_Drop", "urltable", "https://www.spamhaus.org/drop/drop.txt", "Blocklist Spamhaus DROP");
create_alias("BadIPs_EDrop", "urltable", "https://www.spamhaus.org/drop/edrop.txt", "Blocklist Spamhaus EDROP");

// ----------------------------------------------------------------------
// 2. Criar Regras de Firewall (WAN)
// ----------------------------------------------------------------------
// Nota: Adicionaremos regras no topo da interface WAN

if (!is_array($config["filter"]["rule"])) {
    $config["filter"]["rule"] = array();
}

// Regra 1: Bloquear BadIPs (Topo)
$block_rule = array();
$block_rule["type"] = "block";
$block_rule["interface"] = "wan";
$block_rule["ipprotocol"] = "inet";
$block_rule["tag"] = "";
$block_rule["tagged"] = "";
$block_rule["max"] = "";
$block_rule["max-src-nodes"] = "";
$block_rule["max-src-conn"] = "";
$block_rule["max-src-states"] = "";
$block_rule["statetimeout"] = "";
$block_rule["statetype"] = "keep state";
$block_rule["os"] = "";
$block_rule["source"] = array("address" => "BadIPs_Drop"); // Usa o Alias criado
$block_rule["destination"] = array("any" => "");
$block_rule["descr"] = "Bloquear Spamhaus DROP (Auto)";
$block_rule["log"] = "yes"; // Logar bloqueios
$block_rule["created"] = make_config_revision_entry(null, "Script Auto Setup");

// Inserir no início do array de regras (Prioridade Alta)
array_unshift($config["filter"]["rule"], $block_rule);
echo "Regra de bloqueio WAN adicionada (BadIPs_Drop).\n";

// ----------------------------------------------------------------------
// 3. Configurações Avançadas (System Tunables para Anti-DDoS)
// ----------------------------------------------------------------------
if (!is_array($config["sysctl"]["item"])) {
    $config["sysctl"]["item"] = array();
}

function set_tunable($tunable, $value, $descr) {
    global $config;
    foreach ($config["sysctl"]["item"] as $key => $item) {
        if ($item["tunable"] == $tunable) {
            $config["sysctl"]["item"][$key]["value"] = $value;
            echo "Tunable $tunable atualizado para $value.\n";
            return;
        }
    }
    // Se não existir, cria
    $new_tunable = array();
    $new_tunable["tunable"] = $tunable;
    $new_tunable["value"] = $value;
    $new_tunable["descr"] = $descr;
    $config["sysctl"]["item"][] = $new_tunable;
    echo "Tunable $tunable criado ($value).\n";
}

// Aumentar tabela de estados (mitigar state exhaustion attacks)
set_tunable("net.pf.states_hashsize", "2097152", "Aumentar hashsize para firewall states (Script)");
set_tunable("net.pf.source_nodes_hashsize", "524288", "Aumentar hashsize para source nodes (Script)");
set_tunable("debug.pfftpproxy", "0", "Desabilitar ftp proxy debug");

// ----------------------------------------------------------------------
// Salvar e Aplicar
// ----------------------------------------------------------------------
echo "Salvando configurações...\n";
write_config("Regras de Firewall adicionadas via script AI Assistant");

echo "Aplicando filtro (Reload)...\n";
filter_configure();

echo "Concluído! Verifique as regras na interface Web.\n";
?>
