# Vigia Fundo Ambiental

Corre no GitHub Actions de 5 em 5 min e envia push para o tópico ntfy `alerta-fa-veiculos-rafael-2026`.

1. Instala a app ntfy no telemóvel e subscreve o tópico.
2. Cria um repositório **vazio** em https://github.com/new (ex.: `fundo-ambiental`).
3. Liga e faz push (troca `O_TEU_USER`):

```
git remote add origin https://github.com/O_TEU_USER/fundo-ambiental.git
git push -u origin main
```

4. No GitHub: aba **Actions** > ativar workflows > `vigia` > *Run workflow*.
5. Teste local de notificação: `python monitor.py --teste`

Notas: a 1.ª execução só guarda a base (`estado.json`), sem alerta. O cron do GitHub pode atrasar uns minutos; repositórios sem atividade durante 60 dias têm o agendamento pausado (o commit do estado conta como atividade só quando muda).
