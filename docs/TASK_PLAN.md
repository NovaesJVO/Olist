# TASK PLAN: Implementação de SPEC 01 - Ingestão de Dados Olist

**Data**: 2026-06-26  
**Status**: Em Planejamento  

---

## Objetivo

Executar a especificação SPEC 01 para baixar os 9 CSVs originais do dataset Olist (Kaggle) e organizá-los em `dados_originais/`.

---

## Pré-Requisitos

- [x] **Kaggle Dataset**
  - Download realizado em 2026-06-26
  - Arquivo: `archive.zip`
  - Destino: `dados_originais/`
  - Status: ✅ **CONCLUÍDO**

- [ ] **Validação e Próximas Etapas**
  - DDL Bronze (Spec 02)
  - Ingestão ETL (Spec 03)

---

## Tarefas

### Fase 1: Setup

| # | Tarefa | Responsável | Status | Notas |
|---|--------|-------------|--------|-------|
| 1.1 | Instalar `kaggle` package | Dev | [x] | Via pip |
| 1.2 | Validar arquivo `kaggle.json` | Dev | [x] | Download manual via Kaggle Web |
| 1.3 | Testar conexão Kaggle API | Dev | [x] | Dados extraídos com sucesso |

### Fase 2: Implementação do Download

| # | Tarefa | Responsável | Status | Notas |
|---|--------|-------------|--------|-------|
| 2.1 | Download do dataset Olist | Dev | [x] | Archive.zip obtido |
| 2.2 | Extrair arquivos para `dados_originais/` | Dev | [x] | 9 CSVs extraídos |
| 2.3 | Validar 9 arquivos completos | Dev | [x] | Nomes originais preservados |
| 2.4 | Adicionar `dados_originais/` a `.gitignore` | Dev | [x] | Evitar versionamento de dados brutos |

### Fase 3: Validação

| # | Tarefa | Responsável | Status | Notas |
|---|--------|-------------|--------|-------|
| 3.1 | Contar linhas de cada CSV | QA | [x] | Verificação visual realizada |
| 3.2 | Verificar encoding (UTF-8) | QA | [x] | Nenhum erro detectado |
| 3.3 | Validar estrutura de diretórios | QA | [x] | Pasta `dados_originais/` com 9 arquivos |
| 3.4 | Testar reproduzibilidade | QA | [x] | Dados permanentes e rastreáveis |

### Fase 4: Documentação e Commit

| # | Tarefa | Responsável | Status | Notas |
|---|--------|-------------|--------|-------|
| 4.1 | Atualizar SPEC 01 com status concluído | Dev | [x] | Marcado como ✅ CONCLUÍDO |
| 4.2 | Atualizar TASK_PLAN com progresso | Dev | [x] | Fases 1–3 marcadas como concluídas |
| 4.3 | Adicionar `.gitignore` entry para `dados_originais/` | Dev | [x] | Já presente |
| 4.4 | Commit de atualização | Dev | [ ] | Próxima ação |
| 4.5 | Push para GitHub | Dev | [ ] | Próxima ação |

### Fase 5: Próximos Passos

| # | Tarefa | Responsável | Status | Notas |
|---|--------|-------------|--------|-------|
| 5.1 | Criar SPEC 02 (DDL Bronze) | Dev | [ ] | Tables no PostgreSQL |
| 5.2 | Implementar `sql/ddl_bronze.sql` | Dev | [ ] | CREATE TABLE statements |
| 5.3 | Criar SPEC 03 (Ingestão ETL) | Dev | [ ] | Load CSV → PostgreSQL |
| 5.4 | Iniciar Spec 02 | Dev | [ ] | Próxima atividade |

---

## Detalhes de Implementação

### Script: `ingestion/download_olist.py`

```python
#!/usr/bin/env python3
"""
Download de CSVs do dataset Olist (Kaggle).
Requer autenticação via kaggle.json.
"""

import os
import sys
from pathlib import Path
import kaggle

def main():
    # Config
    dataset = "olistbr/brazilian-ecommerce"
    output_dir = Path("dados_originais")
    
    # Criar diretório
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Diretório: {output_dir}")
    
    # Download
    print(f"⬇️  Baixando {dataset}...")
    try:
        kaggle.api.dataset_download_files(
            dataset,
            path=output_dir,
            unzip=True
        )
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        sys.exit(1)
    
    # Validação
    print("\n✅ Validando arquivos:")
    files = sorted(output_dir.glob("*.csv"))
    
    if not files:
        print("❌ Nenhum arquivo encontrado!")
        sys.exit(1)
    
    total_lines = 0
    for f in files:
        line_count = sum(1 for _ in open(f, encoding='utf-8')) - 1  # Exclui header
        total_lines += line_count
        print(f"   {f.name:45} | {line_count:>10,} linhas")
    
    print(f"\n📊 Total: {len(files)} arquivos | {total_lines:,} linhas\n")
    
    expected_files = 9
    if len(files) != expected_files:
        print(f"⚠️  Esperado {expected_files} arquivos, encontrado {len(files)}")

if __name__ == "__main__":
    main()
```

### Checklist Mínimo para DoD

- [ ] `dados_originais/` contém 9 arquivos CSV
- [ ] Nomes de arquivo correspondem aos nomes originais do Kaggle
- [ ] Contagem de linhas aproximada com valores esperados
- [ ] Nenhum erro de encoding
- [ ] `.gitignore` contém `dados_originais/`
- [ ] Script documentado e testado
- [ ] Commit realizado no GitHub

---

## Estimativa de Tempo

- Setup Kaggle: **15 min**
- Implementação script: **20 min**
- Download (depende da internet): **5–15 min**
- Validação: **10 min**
- Documentação e commit: **10 min**

**Total Estimado**: ~90 min (1.5h)

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|--------|-----------|
| Erro de autenticação Kaggle | MÉDIO | ALTO | Validar `kaggle.json` antes de executar |
| Arquivo corrompido no download | BAIXO | ALTO | Re-tentar download; verificar hash |
| Espaço em disco insuficiente | BAIXO | MÉDIO | Verificar ~100 MB disponível |
| Encoding problem (caracteres especiais) | BAIXO | MÉDIO | Forçar UTF-8 no script |

---

## Referências

- [SPEC 01: Ingestão de Dados](spec01.md)
- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)
- [Dataset Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

---

## Histórico de Atualizações

| Data | Versão | Mudança |
|------|--------|---------|
| 2026-06-26 | 1.0 | Criação do task plan |

---

**Próximo Review**: Após conclusão da Fase 1
