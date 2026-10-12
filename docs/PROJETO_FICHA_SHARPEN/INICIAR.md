# INICIAR · prompt para abrir o projeto numa sessão nova

Abra um terminal novo do Claude Code em `C:\Users\Fernando\Downloads\FDC Capital\Planilhador` e cole:

```
Leia C:\Users\Fernando\Downloads\FDC Capital\Planilhador\docs\PROJETO_FICHA_SHARPEN\INICIAR.md e execute.
```

---

## Para a sessão que está lendo isto

Você vai tocar o **Projeto Ficha Sharpen**: tirar a IA do caminho da aposta, começando pelas casas em uso
em outubro, no ritmo mais rápido possível, com o Feca, dia a dia.

### Leia, nesta ordem

1. `docs/PROJETO_FICHA_SHARPEN/README.md`: objetivo, decisões do Feca, cronograma, regras.
2. `docs/PROJETO_FICHA_SHARPEN/DIARIO.md`: onde o projeto parou. **A última entrada manda.**
3. O arquivo da etapa atual (`01_FICHA_SHARPEN.md`, `02_CASAS_OUTUBRO.md`, `03_REGUA_NUMEROS.md` ou
   `04_DICIONARIO.md`), conforme o diário.
4. O `CLAUDE.md` do repositório, e siga.

### Regras deste projeto (valem acima de hábito)

- **O projeto é independente.** As fontes são: os arquivos desta pasta, o código de hoje, o banco de hoje e o
  mapa de auditoria (`C:\Users\Fernando\Downloads\FDC Capital\Auditorias\mapa_2026-10\claude\MAPA.md`,
  somente leitura). **Planos antigos em `docs/PLANO_*.md` não são fonte** e não decidem nada aqui.
- **Números não podem errar.** Odd, stake e resultado 100% exatos. Descrição não é critério.
- **Uma etapa por vez:** proponha, espere o Feca aprovar, execute. No fim de cada dia (ou etapa), escreva a
  entrada no `DIARIO.md`, com prova (arquivo:linha ou consulta) de cada número.
- **Outra sessão pode estar mexendo no repo.** Rode `git status` antes de editar `app/main.py`,
  `app/repository.py`, `app/database.py` ou a extensão, e confirme com o Feca.
- Backup antes de sobrescrever. Nada de commit, push ou deploy sem o Feca mandar.
- Banco de produção: só leitura para medir.
- Não editar manuais (`global/`, `casas/`) neste projeto.
- Toda mudança nova entra atrás de uma chave por casa, desligada até a virada.
- pt-BR, frases diretas. PowerShell 5.1 (sem `&&`, sem heredoc).

### Primeira ação

Se o `DIARIO.md` disser que a Ficha ainda não foi aprovada (D0): apresente ao Feca as 5 perguntas do §9 de
`01_FICHA_SHARPEN.md`, uma por vez ou todas juntas se ele preferir, e registre as respostas no diário e na
Ficha. Só depois disso escreva código.
